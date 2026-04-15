from __future__ import annotations

from statistics import mean
from typing import Any

IOC_FILES_USER = {"cmd.sh", "cmd.exe"}
IOC_FILES_ADMIN = {"escalate.sh", "escalate.exe"}


class EpisodeMetricsTracker:
    """Tracks interpretable defense metrics from evaluation rollouts."""

    def __init__(self):
        self.recovery_tp = 0
        self.recovery_fp = 0
        self.clean_host_ratios: list[float] = []
        self.host_compromise_streak: dict[str, int] = {}
        self.host_compromise_lengths: list[int] = []
        self.red_impact_count = 0

    def _host_compromised(self, host_data: dict[str, Any]) -> bool:
        files = host_data.get("Files", []) if isinstance(host_data, dict) else []
        for file_info in files:
            if not isinstance(file_info, dict):
                continue
            fname = str(file_info.get("File Name", "")).lower()
            if fname in IOC_FILES_USER or fname in IOC_FILES_ADMIN:
                return True

        sessions = host_data.get("Sessions", []) if isinstance(host_data, dict) else []
        if isinstance(sessions, list) and len(sessions) > 1:
            return True

        processes = host_data.get("Processes", []) if isinstance(host_data, dict) else []
        remote_seen: set[str] = set()
        for proc in processes:
            if not isinstance(proc, dict):
                continue
            if "PID" in proc and "username" not in proc:
                return True
            for conn in proc.get("Connections", []) or []:
                if not isinstance(conn, dict):
                    continue
                remote = conn.get("remote_address")
                if remote:
                    remote_str = str(remote)
                    if remote_str in remote_seen:
                        return True
                    remote_seen.add(remote_str)
        return False

    def extract_host_statuses(self, observations: dict[str, Any]) -> dict[str, bool]:
        statuses: dict[str, bool] = {}
        for _, agent_obs in observations.items():
            if not isinstance(agent_obs, dict):
                continue
            for host_key, host_data in agent_obs.items():
                if host_key in {"success", "action", "phase", "message"}:
                    continue
                if not isinstance(host_data, dict):
                    continue
                sys_info = host_data.get("System info", {})
                hostname = str(sys_info.get("Hostname", host_key))
                statuses[hostname] = self._host_compromised(host_data)
        return statuses

    def _update_recovery_precision(self, actions: dict[str, Any], pre_status: dict[str, bool]):
        for _, action in actions.items():
            name = action.__class__.__name__.lower()
            if name not in {"remove", "restore"}:
                continue
            target = getattr(action, "hostname", None)
            if not target:
                self.recovery_fp += 1
                continue
            if pre_status.get(str(target), False):
                self.recovery_tp += 1
            else:
                self.recovery_fp += 1

    def _update_clean_hosts_ratio(self, post_status: dict[str, bool]):
        if not post_status:
            return
        clean_count = sum(1 for compromised in post_status.values() if not compromised)
        self.clean_host_ratios.append(float(clean_count) / float(len(post_status)))

    def _update_mttr(self, post_status: dict[str, bool]):
        observed_hosts = set(post_status.keys())
        for host in observed_hosts:
            compromised = bool(post_status.get(host, False))
            if compromised:
                self.host_compromise_streak[host] = self.host_compromise_streak.get(host, 0) + 1
            else:
                streak = self.host_compromise_streak.get(host, 0)
                if streak > 0:
                    self.host_compromise_lengths.append(streak)
                    self.host_compromise_streak[host] = 0

    def _update_red_impact_count(self, cyborg):
        try:
            for agent_name in getattr(cyborg, "agents", []):
                if "red" not in str(agent_name):
                    continue
                red_action = cyborg.get_last_action(agent_name)
                red_action_name = red_action.__class__.__name__.lower()
                if "impact" in red_action_name:
                    self.red_impact_count += 1
                    return
        except Exception:
            return

    def step(self, pre_status: dict[str, bool], actions: dict[str, Any], post_observations: dict[str, Any], cyborg):
        post_status = self.extract_host_statuses(post_observations)
        self._update_recovery_precision(actions, pre_status)
        self._update_clean_hosts_ratio(post_status)
        self._update_mttr(post_status)
        self._update_red_impact_count(cyborg)

    def finalize(self) -> dict[str, float | int]:
        for host, streak in self.host_compromise_streak.items():
            if streak > 0:
                self.host_compromise_lengths.append(streak)
                self.host_compromise_streak[host] = 0

        total_recovery = self.recovery_tp + self.recovery_fp
        recovery_precision = float(self.recovery_tp) / float(total_recovery) if total_recovery else 0.0
        recovery_error = float(self.recovery_fp) / float(total_recovery) if total_recovery else 0.0
        clean_hosts = mean(self.clean_host_ratios) if self.clean_host_ratios else 0.0
        mttr = mean(self.host_compromise_lengths) if self.host_compromise_lengths else 0.0

        return {
            "recovery_precision": recovery_precision,
            "recovery_error": recovery_error,
            "recovery_true_positive": self.recovery_tp,
            "recovery_false_positive": self.recovery_fp,
            "clean_hosts_mean": clean_hosts,
            "mttr": mttr,
            "red_impact_count": self.red_impact_count,
        }
