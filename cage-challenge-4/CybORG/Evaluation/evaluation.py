import inspect
import time
from statistics import mean, stdev

from CybORG import CybORG, CYBORG_VERSION
from CybORG.Agents import SleepAgent, EnterpriseGreenAgent, FiniteStateRedAgent
from CybORG.Agents.SimpleAgents.AggressiveFSMAgent import AggressiveFSMAgent
from CybORG.Agents.SimpleAgents.StealthyFSMAgent import StealthyFSMAgent
from CybORG.Agents.SimpleAgents.ImpactFSMAgent import ImpactFSMAgent
from CybORG.Agents.SimpleAgents.DegradeServiceFSMAgent import DegradeServiceFSMAgent
from CybORG.Simulator.Scenarios import EnterpriseScenarioGenerator

from datetime import datetime

import json

import sys
import os

from CybORG.Agents.LLMAgents.llm_adapter.metrics_tracker import EpisodeMetricsTracker


def _to_bool(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _strict_baseline_guard(max_eps: int, episode_length: int):
    strict_mode = _to_bool(os.environ.get("CAGE4_ENFORCE_STRICT_BASELINE"))
    if not strict_mode:
        return

    expected_max_eps = int(os.environ.get("CAGE4_BASELINE_MAX_EPS", "2"))
    expected_episode_length = int(os.environ.get("CAGE4_BASELINE_EPISODE_LENGTH", "500"))

    if max_eps != expected_max_eps:
        raise ValueError(
            "Strict baseline mismatch: "
            f"max_eps={max_eps}, expected={expected_max_eps}."
        )
    if episode_length != expected_episode_length:
        raise ValueError(
            "Strict baseline mismatch: "
            f"episode_length={episode_length}, expected={expected_episode_length}."
        )


def _resolve_red_agent_variant() -> tuple[str, type]:
    variant = os.environ.get("CAGE4_RED_AGENT_VARIANT", "finite_state").strip().lower()
    alias_map = {
        "b_line": "aggressive",
        "bline": "aggressive",
        "meander": "stealthy",
    }
    variant = alias_map.get(variant, variant)
    red_variant_to_class = {
        "finite_state": FiniteStateRedAgent,
        "aggressive": AggressiveFSMAgent,
        "stealthy": StealthyFSMAgent,
        "impact": ImpactFSMAgent,
        "degrade_service": DegradeServiceFSMAgent,
    }
    if variant not in red_variant_to_class:
        valid = ", ".join(sorted(red_variant_to_class.keys()))
        raise ValueError(f"Unknown red variant '{variant}'. Valid values: {valid}")
    return variant, red_variant_to_class[variant]


def _resolve_scenario_id() -> str:
    return os.environ.get("CAGE4_BLUE_SCENARIO_ID", "scenario_1")


def _collect_llm_hallucination_metrics(submission) -> dict[str, int]:
    keys = [
        "syntactic_hallucination_count",
        "semantic_hallucination_count",
        "repair_attempt_count",
        "repair_success_count",
        "fallback_sleep_count",
        "total_structured_calls",
    ]
    totals = {k: 0 for k in keys}

    for _, agent in submission.AGENTS.items():
        policy = getattr(agent, "policy", None)
        model_manager = getattr(policy, "model_manager", None)
        if model_manager is None:
            continue
        metrics_getter = getattr(model_manager, "get_hallucination_metrics", None)
        if not callable(metrics_getter):
            continue
        values = metrics_getter() or {}
        for key in keys:
            totals[key] += int(values.get(key, 0))

    return totals


def _diff_metrics(after: dict[str, int], before: dict[str, int]) -> dict[str, int]:
    keys = set(after.keys()) | set(before.keys())
    return {k: int(after.get(k, 0)) - int(before.get(k, 0)) for k in keys}


def rmkdir(path: str):
    """Recursive mkdir"""
    partial_path = ""
    for p in path.split("/"):
        partial_path += p + "/"

        if os.path.exists(partial_path):
            if os.path.isdir(partial_path):
                continue
            if os.path.isfile(partial_path):
                raise RuntimeError(f"Cannot create {partial_path} (exists as file).")

        os.mkdir(partial_path)


def load_submission(source: str):
    """Load submission from a directory or zip file"""
    sys.path.insert(0, source)

    if source.endswith(".zip"):
        try:
            # Load submission from zip.
            from submission.submission import Submission
        except ImportError as e:
            raise ImportError(
                """
                Error loading submission from zip.
                Please ensure the zip contains the path submission/submission.py
                """
            ).with_traceback(e.__traceback__)
    else:
        # Load submission normally
        from submission import Submission

    # Remove submission from path.
    sys.path.remove(source)
    return Submission


def run_evaluation(submission, log_path, max_eps=100, write_to_file=True, seed=None):
    cyborg_version = CYBORG_VERSION
    EPISODE_LENGTH = int(os.environ.get("CAGE_EPISODE_LENGTH", "500"))
    _strict_baseline_guard(max_eps=max_eps, episode_length=EPISODE_LENGTH)

    profile_name = os.environ.get("CAGE4_EXPERIMENT_PROFILE_NAME", "quick")
    strict_mode = _to_bool(os.environ.get("CAGE4_ENFORCE_STRICT_BASELINE"))
    strict_baseline = {
        "max_eps": int(os.environ.get("CAGE4_BASELINE_MAX_EPS", "2")),
        "episode_length": int(os.environ.get("CAGE4_BASELINE_EPISODE_LENGTH", "500")),
    }

    scenario = "Scenario4"
    scenario_id = _resolve_scenario_id()
    red_variant, red_agent_class = _resolve_red_agent_variant()

    version_header = f"CybORG v{cyborg_version}, {scenario}"
    author_header = f"Author: {submission.NAME}, Team: {submission.TEAM}, Technique: {submission.TECHNIQUE}"

    sg = EnterpriseScenarioGenerator(
        blue_agent_class=SleepAgent,
        green_agent_class=EnterpriseGreenAgent,
        red_agent_class=red_agent_class,
        steps=EPISODE_LENGTH,
    )
    cyborg = CybORG(sg, "sim", seed=seed)
    wrapped_cyborg = submission.wrap(cyborg)
    
    print(version_header)
    print(author_header)
    print(f"Experiment profile: {profile_name} (strict_mode={strict_mode})")
    print(f"Scenario ID: {scenario_id} | Red variant: {red_variant} ({red_agent_class.__name__})")
    print(
        f"Using agents {submission.AGENTS}, if this is incorrect please update the code to load in your agent"
    )

    if write_to_file:
        if not log_path.endswith("/"):
            log_path += "/"
        print(f"Results will be saved to {log_path}")

    start = datetime.now()

    total_reward = []
    episode_hallucination_metrics = []
    episode_defense_metrics = []
    actions_log = []
    obs_log = []
    for i in range(max_eps):
        hallucination_before = _collect_llm_hallucination_metrics(submission)
        observations, _ = wrapped_cyborg.reset()
        metrics_tracker = EpisodeMetricsTracker()
        r = []
        a = []
        o = []
        count = 0
        for j in range(EPISODE_LENGTH):
            pre_status = metrics_tracker.extract_host_statuses(observations)
            actions = {
                agent_name: agent.get_action(
                    observations[agent_name], wrapped_cyborg.action_space(agent_name)
                )
                for agent_name, agent in submission.AGENTS.items()
                if agent_name in wrapped_cyborg.agents
            }
            observations, rew, term, trunc, info = wrapped_cyborg.step(actions)
            metrics_tracker.step(pre_status=pre_status, actions=actions, post_observations=observations, cyborg=cyborg)
            done = {
                agent: term.get(agent, False) or trunc.get(agent, False)
                for agent in wrapped_cyborg.agents
            }
            if all(done.values()):
                break
            r.append(mean(rew.values()))
            if write_to_file:
                a.append(
                    {
                        agent_name: cyborg.get_last_action(agent_name)
                        for agent_name in wrapped_cyborg.agents
                    }       
                )
                o.append(
                    {
                        agent_name: observations[agent_name]
                        for agent_name in observations.keys()
                    }
                )
        total_reward.append(sum(r))
        hallucination_after = _collect_llm_hallucination_metrics(submission)
        episode_hallucination_metrics.append(_diff_metrics(hallucination_after, hallucination_before))
        episode_defense_metrics.append(metrics_tracker.finalize())

        if write_to_file:
            actions_log.append(a)
            obs_log.append(o)

    end = datetime.now()
    difference = end - start

    reward_mean = mean(total_reward)
    reward_stdev = stdev(total_reward)
    hallucination_totals = {
        "syntactic_hallucination_count": sum(m.get("syntactic_hallucination_count", 0) for m in episode_hallucination_metrics),
        "semantic_hallucination_count": sum(m.get("semantic_hallucination_count", 0) for m in episode_hallucination_metrics),
        "repair_attempt_count": sum(m.get("repair_attempt_count", 0) for m in episode_hallucination_metrics),
        "repair_success_count": sum(m.get("repair_success_count", 0) for m in episode_hallucination_metrics),
        "fallback_sleep_count": sum(m.get("fallback_sleep_count", 0) for m in episode_hallucination_metrics),
        "total_structured_calls": sum(m.get("total_structured_calls", 0) for m in episode_hallucination_metrics),
    }
    total_calls = max(1, hallucination_totals["total_structured_calls"])
    total_hallucinations = (
        hallucination_totals["syntactic_hallucination_count"]
        + hallucination_totals["semantic_hallucination_count"]
    )
    hallucination_rate = float(total_hallucinations) / float(total_calls)
    aggregate_defense_metrics = {
        "recovery_precision": mean([m["recovery_precision"] for m in episode_defense_metrics]) if episode_defense_metrics else 0.0,
        "recovery_error": mean([m["recovery_error"] for m in episode_defense_metrics]) if episode_defense_metrics else 0.0,
        "clean_hosts_mean": mean([m["clean_hosts_mean"] for m in episode_defense_metrics]) if episode_defense_metrics else 0.0,
        "mttr": mean([m["mttr"] for m in episode_defense_metrics]) if episode_defense_metrics else 0.0,
        "red_impact_count": sum(m["red_impact_count"] for m in episode_defense_metrics),
        "recovery_true_positive": sum(m["recovery_true_positive"] for m in episode_defense_metrics),
        "recovery_false_positive": sum(m["recovery_false_positive"] for m in episode_defense_metrics),
        "episodes": episode_defense_metrics,
    }
    reward_string = (
        f"Average reward is: {reward_mean} with a standard deviation of {reward_stdev}"
    )
    print(reward_string)
    print(
        "Hallucination metrics: "
        f"syntactic={hallucination_totals['syntactic_hallucination_count']}, "
        f"semantic={hallucination_totals['semantic_hallucination_count']}, "
        f"rate={hallucination_rate:.6f}"
    )
    print(
        "Defense metrics: "
        f"recovery_precision={aggregate_defense_metrics['recovery_precision']:.6f}, "
        f"clean_hosts_mean={aggregate_defense_metrics['clean_hosts_mean']:.6f}, "
        f"mttr={aggregate_defense_metrics['mttr']:.6f}, "
        f"red_impact_count={aggregate_defense_metrics['red_impact_count']}"
    )

    print(f"File took {difference} amount of time to finish evaluation")
    if write_to_file:
        print(f"Saving results to {log_path}")
        with open(log_path + "summary.txt", "w") as data:
            data.write(version_header + "\n")
            data.write(author_header + "\n")
            data.write(reward_string + "\n")
            data.write(f"Using agents {submission.AGENTS}")

        with open(log_path + "full.txt", "w") as data:
            data.write(version_header + "\n")
            data.write(author_header + "\n")
            data.write(reward_string + "\n")
            for act, obs, sum_rew in zip(actions_log, obs_log, total_reward):
                data.write(
                    f"actions: {act},\n observations: {obs},\n total reward: {sum_rew}\n"
                )
        
        with open(log_path + "actions.txt", "w") as data:
            data.write(version_header + "\n")
            data.write(author_header + "\n")
            data.write(reward_string + "\n")
            for act in zip(actions_log):
                data.write(
                    f"actions: {act}"
                )

        with open(log_path + "summary.json", "w") as output:
            data = {
                "submission": {
                    "author": submission.NAME,
                    "team": submission.TEAM,
                    "technique": submission.TECHNIQUE,
                },
                "parameters": {
                    "seed": seed,
                    "episode_length": EPISODE_LENGTH,
                    "max_episodes": max_eps,
                    "scenario": {
                        "name": scenario,
                        "id": scenario_id,
                    },
                    "red_agent": {
                        "variant": red_variant,
                        "class": red_agent_class.__name__,
                    },
                    "profile": {
                        "name": profile_name,
                        "strict_mode": strict_mode,
                        "strict_baseline": strict_baseline,
                    },
                },
                "time": {
                    "start": str(start),
                    "end": str(end),
                    "elapsed": str(difference),
                },
                "reward": {
                    "mean": reward_mean,
                    "stdev": reward_stdev,
                },
                "hallucination": {
                    **hallucination_totals,
                    "total_hallucination_count": total_hallucinations,
                    "hallucination_rate": hallucination_rate,
                    "episodes": episode_hallucination_metrics,
                },
                "defense_metrics": aggregate_defense_metrics,
                "agents": {
                    agent: str(submission.AGENTS[agent]) for agent in submission.AGENTS
                },
            }
            json.dump(data, output)

        with open(log_path + "run_profile.json", "w") as output:
            data = {
                "name": profile_name,
                "strict_mode": strict_mode,
                "strict_baseline": strict_baseline,
                "effective": {
                    "max_eps": max_eps,
                    "episode_length": EPISODE_LENGTH,
                    "scenario_name": scenario,
                    "scenario_id": scenario_id,
                    "red_variant": red_variant,
                    "red_agent_class": red_agent_class.__name__,
                },
            }
            json.dump(data, output, indent=2)

        with open(log_path + "scores.txt", "w") as scores:
            scores.write(f"reward_mean: {reward_mean}\n")
            scores.write(f"reward_stdev: {reward_stdev}\n")
            scores.write(f"hallucination_rate: {hallucination_rate}\n")
            scores.write(f"recovery_precision: {aggregate_defense_metrics['recovery_precision']}\n")
            scores.write(f"clean_hosts_mean: {aggregate_defense_metrics['clean_hosts_mean']}\n")
            scores.write(f"mttr: {aggregate_defense_metrics['mttr']}\n")
            scores.write(f"red_impact_count: {aggregate_defense_metrics['red_impact_count']}\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser("CybORG Evaluation Script")
    parser.add_argument("submission_path", type=str)
    parser.add_argument("output_path", type=str)
    parser.add_argument(
        "--append-timestamp",
        action="store_true",
        help="Appends timestamp to output_path",
    )
    parser.add_argument(
        "--seed", type=int, default=None, help="Set the seed for CybORG"
    )
    parser.add_argument("--max-eps", type=int, default=100, help="Max episodes to run")
    args = parser.parse_args()
    args.output_path = os.path.abspath(args.output_path)
    args.submission_path = os.path.abspath(args.submission_path)

    if not args.output_path.endswith("/"):
        args.output_path += "/"

    if args.append_timestamp:
        args.output_path += time.strftime("%Y%m%d_%H%M%S") + "/"

    rmkdir(args.output_path)

    submission = load_submission(args.submission_path)
    run_evaluation(
        submission, max_eps=args.max_eps, log_path=args.output_path, seed=args.seed
    )
