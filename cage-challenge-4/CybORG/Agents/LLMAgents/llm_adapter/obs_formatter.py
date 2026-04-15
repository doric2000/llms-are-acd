from __future__ import annotations

from typing import Any

from CybORG.Agents.LLMAgents.llm_adapter.utils.logger import Logger


SYSTEM_KEYS = {"success", "action", "phase", "message"}
IOC_FILES_USER = {"cmd.sh", "cmd.exe"}
IOC_FILES_ADMIN = {"escalate.sh", "escalate.exe"}


def _format_comm_vector_message(agent_name: str, commvectors: Any) -> list[str]:
    """Format commvector messages from peer blue agents."""
    text_obs: list[str] = []

    if not isinstance(commvectors, (list, tuple)):
        return ["Commvector Blue Agents: unavailable"]

    try:
        agent_number = int(agent_name[-1])
    except Exception:
        agent_number = -1

    agent_indices = [idx for idx in range(5) if idx != agent_number]
    for idx, vector in zip(agent_indices, commvectors):
        try:
            vector_items = list(vector)
            binary_array = [1 if bool(x) else 0 for x in vector_items]
        except TypeError:
            binary_array = [1 if bool(vector) else 0]
        text_obs.append(f"Commvector Blue Agent {idx} Message: {binary_array}")

    if not text_obs:
        text_obs.append("Commvector Blue Agents: unavailable")
    return text_obs


def _ioc_label(priority: int) -> str:
    labels = {
        0: "clean",
        1: "reconnaissance/anomalous",
        2: "exploit/user-level compromise",
        3: "privilege-escalation/admin compromise",
    }
    return labels.get(priority, "unknown")


def _infer_zone(hostname: str) -> str:
    name = hostname.lower()
    if "operational" in name:
        return "Operational Zone"
    if "restricted" in name:
        return "Restricted Zone"
    if "public" in name:
        return "Public Access Zone"
    if "admin" in name or "hq" in name:
        return "HQ/Admin Network"
    if "office" in name or "corp" in name:
        return "Corporate/Office Zone"
    return "Unknown Zone"


def _extract_host_signal(host_key: str, host_data: dict[str, Any]) -> dict[str, Any]:
    sys_info = host_data.get("System info", {}) if isinstance(host_data, dict) else {}
    hostname = str(sys_info.get("Hostname", host_key))

    suspicious_processes = False
    suspicious_connections = False
    suspicious_sessions = False
    evidence: list[str] = []
    ioc_priority = 0

    processes = host_data.get("Processes", []) if isinstance(host_data, dict) else []
    remote_addresses: set[str] = set()
    for proc in processes:
        if not isinstance(proc, dict):
            continue

        if "PID" in proc and "username" not in proc:
            suspicious_processes = True
            ioc_priority = max(ioc_priority, 1)
            evidence.append("process with PID but missing owner")

        for conn in proc.get("Connections", []) or []:
            if not isinstance(conn, dict):
                continue
            remote = conn.get("remote_address")
            if remote:
                remote_str = str(remote)
                if remote_str in remote_addresses:
                    suspicious_connections = True
                    ioc_priority = max(ioc_priority, 1)
                    evidence.append(f"repeated remote connection from {remote_str}")
                remote_addresses.add(remote_str)

    sessions = host_data.get("Sessions", []) if isinstance(host_data, dict) else []
    if isinstance(sessions, list) and len(sessions) > 1:
        suspicious_sessions = True
        ioc_priority = max(ioc_priority, 2)
        evidence.append("multiple active sessions")

    files = host_data.get("Files", []) if isinstance(host_data, dict) else []
    for file_info in files:
        if not isinstance(file_info, dict):
            continue
        fname = str(file_info.get("File Name", "")).lower()
        if fname in IOC_FILES_ADMIN:
            ioc_priority = 3
            evidence.append(f"admin IOC file {fname}")
        elif fname in IOC_FILES_USER:
            ioc_priority = max(ioc_priority, 2)
            evidence.append(f"user IOC file {fname}")

    zone = _infer_zone(hostname)
    if zone == "Operational Zone" and ioc_priority >= 1:
        proximity = "CRITICAL: 1 hop from likely OT/mission services"
    elif zone in {"HQ/Admin Network", "Restricted Zone"} and ioc_priority >= 1:
        proximity = "HIGH: close to sensitive management paths"
    else:
        proximity = "NORMAL"

    return {
        "hostname": hostname,
        "zone": zone,
        "ioc_priority": ioc_priority,
        "ioc_label": _ioc_label(ioc_priority),
        "suspicious_processes": suspicious_processes,
        "suspicious_connections": suspicious_connections,
        "suspicious_sessions": suspicious_sessions,
        "evidence": evidence,
        "proximity": proximity,
    }


def _collect_host_signals(observation: dict[str, Any]) -> list[dict[str, Any]]:
    hosts: list[dict[str, Any]] = []
    for key, value in observation.items():
        if key in SYSTEM_KEYS or not isinstance(value, dict):
            continue
        hosts.append(_extract_host_signal(str(key), value))

    return sorted(hosts, key=lambda h: (h["zone"], -int(h["ioc_priority"]), h["hostname"]))


def _format_topology_section(hosts: list[dict[str, Any]]) -> list[str]:
    lines = ["# NETWORK TOPOLOGY"]
    if not hosts:
        lines.append("- Topology unavailable")
        return lines

    zone_hosts: dict[str, list[str]] = {}
    for host in hosts:
        zone_hosts.setdefault(str(host["zone"]), []).append(str(host["hostname"]))

    for zone in sorted(zone_hosts.keys()):
        host_list = ", ".join(sorted(zone_hosts[zone]))
        lines.append(f"- {zone}: [{host_list}]")

    lines.append("- Priority path hint: Operational Zone hosts are closest to mission/OT services.")
    return lines


def _format_ioc_summary_section(hosts: list[dict[str, Any]]) -> list[str]:
    lines = ["# IOC SUMMARY"]
    if not hosts:
        lines.append("- No host telemetry available")
        return lines

    for host in hosts:
        lines.append(
            "- Host: {hostname} | Zone: {zone} | IOC Priority: {prio} ({label}) | "
            "SuspiciousProcesses={proc} | SuspiciousConnections={conn} | "
            "SuspiciousSessions={sess} | Proximity={prox}".format(
                hostname=host["hostname"],
                zone=host["zone"],
                prio=host["ioc_priority"],
                label=host["ioc_label"],
                proc=host["suspicious_processes"],
                conn=host["suspicious_connections"],
                sess=host["suspicious_sessions"],
                prox=host["proximity"],
            )
        )
        evidence = host["evidence"]
        if evidence:
            lines.append(f"  Evidence: {', '.join(evidence)}")

    return lines


def format_observation(observation: dict[str, Any] | None, last_action: str | None, agent_name: str) -> str:
    """Format CybORG observation into deterministic text for the LLM."""
    if observation is None:
        return "No observation available. Choose a defensive action."

    Logger.debug("Received observation")
    text_obs: list[str] = []

    phase = observation.get("phase", "unknown")
    success = observation.get("success", "unknown")
    text_obs.append(f"Mission Phase: {phase}")
    text_obs.append(f"Last Action: {last_action if last_action is not None else 'None'}")
    text_obs.append(f"Last Action Status: {success}")

    text_obs.append("# COMMUNICATION VECTORS")
    commvectors = observation.get("message")
    text_obs.extend(_format_comm_vector_message(agent_name, commvectors))

    host_signals = _collect_host_signals(observation)
    text_obs.extend(_format_topology_section(host_signals))
    text_obs.extend(_format_ioc_summary_section(host_signals))

    formatted_obs = "# OBSERVATION\n\n" + "\n".join(text_obs)
    Logger.debug(f"Formatted observation:\n{formatted_obs}\n")
    return formatted_obs
