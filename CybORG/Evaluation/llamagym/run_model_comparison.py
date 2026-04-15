from __future__ import annotations

import argparse
import json
import os
import queue
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from statistics import mean, stdev
from typing import Any


STRICT_BASELINE_MAX_EPS = 2
STRICT_BASELINE_EPISODE_LENGTH = 500


@dataclass
class ModelRunResult:
    name: str
    config_path: str
    output_dir: str
    case_id: str
    red_variant: str | None
    scenario_seed: int | None
    scenario_id: str | None
    return_code: int
    summary: dict[str, Any] | None
    elapsed: str | None
    reward_mean: float | None
    reward_stdev: float | None
    hallucination_rate: float | None


RED_VARIANT_TO_CLASS = {
    "finite_state": "FiniteStateRedAgent",
    "aggressive": "AggressiveFSMAgent",
    "stealthy": "StealthyFSMAgent",
    "impact": "ImpactFSMAgent",
    "degrade_service": "DegradeServiceFSMAgent",
}


def _resolve_defaults() -> tuple[Path, Path, Path, Path, list[str]]:
    repo_root = Path(__file__).resolve().parents[3]
    eval_workspace = repo_root / "cage-challenge-4"
    submission_path = eval_workspace / "CybORG" / "Evaluation" / "llamagym"
    model_config_dir = repo_root / "CybORG" / "Agents" / "LLMAgents" / "config" / "model"
    default_models = ["deepseek-r1-1.5b", "qwen2.5-7b"]
    return repo_root, eval_workspace, submission_path, model_config_dir, default_models


def _resolve_profile_settings(args: argparse.Namespace) -> tuple[str, int, int]:
    profile = args.profile
    if args.quick:
        # Backward compatibility for existing scripts.
        profile = "quick"

    if profile == "strict":
        if args.max_eps != STRICT_BASELINE_MAX_EPS:
            raise ValueError(
                "Strict profile requires --max-eps=2 to match the paper baseline. "
                f"Received --max-eps={args.max_eps}."
            )
        if args.episode_length is not None and args.episode_length != STRICT_BASELINE_EPISODE_LENGTH:
            raise ValueError(
                "Strict profile requires --episode-length=500 to match the paper baseline. "
                f"Received --episode-length={args.episode_length}."
            )
        return profile, STRICT_BASELINE_MAX_EPS, STRICT_BASELINE_EPISODE_LENGTH

    max_eps = args.max_eps
    if max_eps < 2:
        print("[INFO] For compatibility with evaluation.py statistics, forcing max_eps=2.")
        max_eps = 2
    episode_length = args.episode_length if args.episode_length is not None else 5
    return profile, max_eps, episode_length


def _resolve_models(model_config_dir: Path, model_names: list[str]) -> list[tuple[str, Path]]:
    models: list[tuple[str, Path]] = []
    missing: list[str] = []
    for model_name in model_names:
        cfg_path = model_config_dir / f"{model_name}.yml"
        if cfg_path.exists():
            models.append((model_name, cfg_path))
        else:
            missing.append(model_name)

    if missing:
        available = sorted(p.stem for p in model_config_dir.glob("*.yml"))
        raise ValueError(
            "Unknown model config(s): "
            + ", ".join(missing)
            + ". Available configs: "
            + ", ".join(available)
        )
    return models


def _parse_csv(values: str | None) -> list[str]:
    if values is None:
        return []
    return [item.strip() for item in values.split(",") if item.strip()]


def _resolve_red_variants(args: argparse.Namespace) -> list[str]:
    variants = _parse_csv(args.red_variants)
    if not variants:
        if args.matrix == "paper":
            variants = list(RED_VARIANT_TO_CLASS.keys())
        else:
            variants = ["finite_state"]

    unknown = [v for v in variants if v not in RED_VARIANT_TO_CLASS]
    if unknown:
        raise ValueError(
            "Unknown red variant(s): "
            + ", ".join(unknown)
            + ". Valid values: "
            + ", ".join(sorted(RED_VARIANT_TO_CLASS.keys()))
        )
    return variants


def _resolve_scenario_seeds(args: argparse.Namespace) -> list[int]:
    raw = _parse_csv(args.scenario_seeds)
    if not raw:
        if args.matrix == "paper":
            return [1001, 1002, 1003, 1004]
        return []

    seeds: list[int] = []
    for value in raw:
        try:
            seeds.append(int(value))
        except ValueError as exc:
            raise ValueError(f"Invalid scenario seed '{value}'. Seeds must be integers.") from exc
    return seeds


def _run_single_model(
    repo_root: Path,
    eval_workspace: Path,
    submission_path: Path,
    model_name: str,
    model_cfg: Path,
    run_output_dir: Path,
    max_eps: int,
    episode_length: int,
    heartbeat_sec: int,
    timeout_sec: int,
    wandb_mode: str,
    wandb_entity: str | None,
    run_profile: dict[str, Any],
    case_id: str,
    red_variant: str | None,
    scenario_seed: int | None,
    scenario_id: str | None,
) -> ModelRunResult:
    run_output_dir.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["CAGE4_MODEL_CONFIG"] = str(model_cfg)
    env["CAGE_EPISODE_LENGTH"] = str(episode_length)
    env["CAGE4_MAX_EPS"] = str(max_eps)
    env["CAGE4_DEBUG_MODE"] = "false"
    env["CAGE4_EXPERIMENT_PROFILE_NAME"] = str(run_profile.get("profile_name", "quick"))
    env["CAGE4_ENFORCE_STRICT_BASELINE"] = str(run_profile.get("strict_mode", False)).lower()
    env["CAGE4_BASELINE_MAX_EPS"] = str(run_profile.get("strict_baseline", {}).get("max_eps", STRICT_BASELINE_MAX_EPS))
    env["CAGE4_BASELINE_EPISODE_LENGTH"] = str(
        run_profile.get("strict_baseline", {}).get("episode_length", STRICT_BASELINE_EPISODE_LENGTH)
    )
    env["CAGE4_STEP_TRACE_PATH"] = str(run_output_dir / "step_trace.jsonl")
    env["CAGE4_METRICS_TRACE_PATH"] = str(run_output_dir / "metrics_trace.jsonl")
    env["PYTHONWARNINGS"] = (
        'ignore:Gym has been unmaintained since 2022 and does not support NumPy 2.0 amongst other critical functionality:UserWarning'
    )
    if red_variant is not None:
        env["CAGE4_RED_AGENT_VARIANT"] = red_variant
        env["CAGE4_RED_AGENT_CLASS"] = RED_VARIANT_TO_CLASS[red_variant]
    if scenario_id is not None:
        env["CAGE4_BLUE_SCENARIO_ID"] = scenario_id

    run_profile_path = run_output_dir / "run_profile.json"
    run_profile_path.write_text(json.dumps(run_profile, indent=2), encoding="utf-8")

    cmd = [
        sys.executable,
        "-m",
        "CybORG.Evaluation.evaluation",
        "--max-eps",
        str(max_eps),
    ]
    if scenario_seed is not None:
        cmd.extend(["--seed", str(scenario_seed)])
    cmd.extend([
        str(submission_path),
        str(run_output_dir),
    ])
    # NOTE: The current evaluation script in this repository does not accept
    # wandb CLI flags. We keep these args in the runner interface for future
    # compatibility but intentionally do not forward them here.

    proc = subprocess.Popen(
        cmd,
        cwd=str(eval_workspace),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    stdout_path = run_output_dir / "stdout.log"
    stderr_path = run_output_dir / "stderr.log"

    q: queue.Queue[tuple[str, str]] = queue.Queue()

    def _reader(stream, stream_name: str):
        try:
            for line in iter(stream.readline, ""):
                q.put((stream_name, line))
        finally:
            try:
                stream.close()
            except Exception:
                pass

    def _should_suppress_stderr_line(line: str) -> bool:
        suppressed_fragments = (
            "Gym has been unmaintained since 2022 and does not support NumPy 2.0 amongst other critical functionality.",
            "Please upgrade to Gymnasium, the maintained drop-in replacement of Gym",
            "Users of this version of Gym should be able to simply replace 'import gym' with 'import gymnasium as gym'",
            "See the migration guide at https://gymnasium.farama.org/introduction/migration_guide/ for additional information.",
        )
        return any(fragment in line for fragment in suppressed_fragments)

    t_out = threading.Thread(target=_reader, args=(proc.stdout, "stdout"), daemon=True)
    t_err = threading.Thread(target=_reader, args=(proc.stderr, "stderr"), daemon=True)
    t_out.start()
    t_err.start()

    spinner = "|/-\\"
    spin_idx = 0
    start_ts = time.time()
    last_heartbeat = 0.0
    timed_out = False

    with stdout_path.open("w", encoding="utf-8") as out_f, stderr_path.open("w", encoding="utf-8") as err_f:
        while True:
            try:
                stream_name, line = q.get(timeout=0.25)
                if stream_name == "stdout":
                    out_f.write(line)
                    out_f.flush()
                    print(f"[{model_name}][OUT] {line}", end="")
                else:
                    if _should_suppress_stderr_line(line):
                        continue
                    err_f.write(line)
                    err_f.flush()
                    print(f"[{model_name}][ERR] {line}", end="")
            except queue.Empty:
                pass

            now = time.time()
            elapsed = now - start_ts
            if now - last_heartbeat >= heartbeat_sec:
                spin = spinner[spin_idx % len(spinner)]
                spin_idx += 1
                print(
                    f"[INFO][{model_name}] {spin} running... elapsed={int(elapsed)}s "
                    f"(max_eps={max_eps}, episode_length={episode_length})"
                )
                last_heartbeat = now

            if timeout_sec > 0 and elapsed > timeout_sec and proc.poll() is None and not timed_out:
                timed_out = True
                proc.terminate()
                print(f"[WARN][{model_name}] timed out after {timeout_sec}s; terminating run")

            if proc.poll() is not None:
                # Drain any remaining queued lines quickly.
                while not q.empty():
                    stream_name, line = q.get_nowait()
                    if stream_name == "stdout":
                        out_f.write(line)
                        out_f.flush()
                        print(f"[{model_name}][OUT] {line}", end="")
                    else:
                        if _should_suppress_stderr_line(line):
                            continue
                        err_f.write(line)
                        err_f.flush()
                        print(f"[{model_name}][ERR] {line}", end="")
                break

    t_out.join(timeout=1)
    t_err.join(timeout=1)

    return_code = proc.returncode if proc.returncode is not None else 1
    if timed_out and return_code == 0:
        return_code = 124

    summary_path = run_output_dir / "summary.json"
    summary = None
    elapsed = None
    reward_mean = None
    reward_stdev = None
    hallucination_rate = None

    if summary_path.exists():
        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            elapsed = (summary.get("time") or {}).get("elapsed")
            reward = summary.get("reward") or {}
            reward_mean = reward.get("mean")
            reward_stdev = reward.get("stdev")
            hallucination = summary.get("hallucination") or {}
            hallucination_rate = hallucination.get("hallucination_rate")
        except Exception:
            summary = None

    return ModelRunResult(
        name=model_name,
        config_path=str(model_cfg),
        output_dir=str(run_output_dir),
        case_id=case_id,
        red_variant=red_variant,
        scenario_seed=scenario_seed,
        scenario_id=scenario_id,
        return_code=return_code,
        summary=summary,
        elapsed=elapsed,
        reward_mean=reward_mean,
        reward_stdev=reward_stdev,
        hallucination_rate=hallucination_rate,
    )


def _write_comparison(output_root: Path, results: list[ModelRunResult], run_profile: dict[str, Any]) -> None:
    model_aggregate: dict[str, dict[str, Any]] = {}
    for model_name in sorted({r.name for r in results}):
        rows = [r for r in results if r.name == model_name]
        reward_values = [r.reward_mean for r in rows if r.reward_mean is not None]
        halluc_values = [r.hallucination_rate for r in rows if r.hallucination_rate is not None]
        failed = sum(1 for r in rows if r.return_code != 0)

        if reward_values:
            agg_mean = mean(reward_values)
            agg_std = stdev(reward_values) if len(reward_values) > 1 else 0.0
        else:
            agg_mean = None
            agg_std = None

        agg_hall = mean(halluc_values) if halluc_values else None
        model_aggregate[model_name] = {
            "case_count": len(rows),
            "failed_case_count": failed,
            "reward_mean": agg_mean,
            "reward_stdev": agg_std,
            "hallucination_rate": agg_hall,
        }

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "run_profile": run_profile,
        "models": [
            {
                "name": model_name,
                **model_aggregate[model_name],
            }
            for model_name in sorted(model_aggregate.keys())
        ],
        "cases": [
            {
                "name": r.name,
                "config_path": r.config_path,
                "output_dir": r.output_dir,
                "case_id": r.case_id,
                "red_variant": r.red_variant,
                "scenario_seed": r.scenario_seed,
                "scenario_id": r.scenario_id,
                "return_code": r.return_code,
                "elapsed": r.elapsed,
                "reward_mean": r.reward_mean,
                "reward_stdev": r.reward_stdev,
                "hallucination_rate": r.hallucination_rate,
            }
            for r in results
        ],
    }

    comparison_json = output_root / "comparison.json"
    comparison_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# LLM Model Comparison",
        "",
        f"Generated at: {payload['generated_at']}",
        f"Profile: {run_profile.get('profile_name', 'quick')}",
        (
            "Baseline lock: "
            + (
                f"max_eps={run_profile.get('strict_baseline', {}).get('max_eps', STRICT_BASELINE_MAX_EPS)}, "
                f"episode_length={run_profile.get('strict_baseline', {}).get('episode_length', STRICT_BASELINE_EPISODE_LENGTH)}"
            )
        ),
        f"Matrix mode: {run_profile.get('matrix_mode', 'none')}",
        "",
        "## Aggregate By Model",
        "",
        "| Model | Cases | Failed Cases | Mean Reward | Reward StdDev | Hallucination Rate |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for model_name in sorted(model_aggregate.keys()):
        agg = model_aggregate[model_name]
        mean_txt = "n/a" if agg["reward_mean"] is None else f"{agg['reward_mean']:.4f}"
        std_txt = "n/a" if agg["reward_stdev"] is None else f"{agg['reward_stdev']:.4f}"
        hall_txt = "n/a" if agg["hallucination_rate"] is None else f"{agg['hallucination_rate']:.6f}"
        lines.append(
            f"| {model_name} | {agg['case_count']} | {agg['failed_case_count']} | {mean_txt} | {std_txt} | {hall_txt} |"
        )

    lines.extend(
        [
            "",
            "## Case Results",
            "",
            "| Model | Case | Red Variant | Scenario ID | Scenario Seed | Return Code | Mean Reward | Hallucination Rate | Elapsed |",
            "|---|---|---|---|---:|---:|---:|---:|---|",
        ]
    )
    for r in results:
        mean_txt = "n/a" if r.reward_mean is None else f"{r.reward_mean:.4f}"
        hall_txt = "n/a" if r.hallucination_rate is None else f"{r.hallucination_rate:.6f}"
        seed_txt = "n/a" if r.scenario_seed is None else str(r.scenario_seed)
        elapsed_txt = r.elapsed or "n/a"
        lines.append(
            f"| {r.name} | {r.case_id} | {r.red_variant or 'n/a'} | {r.scenario_id or 'n/a'} | {seed_txt} | {r.return_code} | {mean_txt} | {hall_txt} | {elapsed_txt} |"
        )

    comparison_md = output_root / "comparison.md"
    comparison_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run LLM model comparison for CybORG llamagym submission.")
    parser.add_argument(
        "--profile",
        type=str,
        default="quick",
        choices=["quick", "strict"],
        help="Experiment profile: quick for development or strict for paper-baseline parity.",
    )
    parser.add_argument("--max-eps", type=int, default=2, help="Max episodes per model run.")
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Deprecated alias for --profile quick. Kept for backward compatibility.",
    )
    parser.add_argument(
        "--episode-length",
        type=int,
        default=None,
        help="Episode length override. In strict profile this must remain 500.",
    )
    parser.add_argument("--heartbeat-sec", type=int, default=10, help="Heartbeat interval in seconds for live progress feedback.")
    parser.add_argument("--timeout-sec", type=int, default=0, help="Optional timeout per model run (0 disables timeout).")
    parser.add_argument("--wandb-mode", type=str, default="offline", choices=["offline", "online"], help="Weights & Biases mode.")
    parser.add_argument("--wandb-entity", type=str, default=None, help="Optional wandb entity.")
    parser.add_argument(
        "--matrix",
        type=str,
        default="none",
        choices=["none", "paper"],
        help="Matrix mode: none (single case) or paper (red variants x blue scenario seeds).",
    )
    parser.add_argument(
        "--red-variants",
        type=str,
        default=None,
        help=(
            "Comma-separated red variants: "
            "finite_state,aggressive,stealthy,impact,degrade_service. "
            "Default in --matrix paper is all variants."
        ),
    )
    parser.add_argument(
        "--scenario-seeds",
        type=str,
        default=None,
        help="Comma-separated integer seeds used to represent blue scenarios in matrix runs.",
    )
    parser.add_argument(
        "--models",
        type=str,
        default=None,
        help="Comma-separated model config names (without .yml), e.g. deepseek-r1-1.5b,qwen2.5-7b",
    )
    parser.add_argument(
        "--output-root",
        type=str,
        default=None,
        help="Output root directory. Default: <repo>/.dist/llm_compare/<timestamp>",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root, eval_workspace, submission_path, model_config_dir, default_model_names = _resolve_defaults()

    requested_model_names = default_model_names
    if args.models:
        requested_model_names = [m.strip() for m in args.models.split(",") if m.strip()]
        if not requested_model_names:
            raise ValueError("--models was provided but no valid model names were found")
    models = _resolve_models(model_config_dir, requested_model_names)

    profile_name, max_eps, episode_length = _resolve_profile_settings(args)
    red_variants = _resolve_red_variants(args)
    scenario_seeds = _resolve_scenario_seeds(args)

    if args.matrix == "paper" and len(scenario_seeds) != 4:
        raise ValueError(
            "Paper matrix requires exactly 4 scenario seeds to represent the four blue scenarios. "
            f"Received {len(scenario_seeds)} seeds: {scenario_seeds}"
        )

    matrix_cases: list[dict[str, Any]] = []
    if args.matrix == "paper":
        for red_variant in red_variants:
            for idx, seed in enumerate(scenario_seeds, start=1):
                matrix_cases.append(
                    {
                        "case_id": f"red-{red_variant}__blue-s{idx}",
                        "red_variant": red_variant,
                        "scenario_seed": seed,
                        "scenario_id": f"scenario_{idx}",
                    }
                )
    else:
        matrix_cases.append(
            {
                "case_id": "single",
                "red_variant": red_variants[0] if red_variants else None,
                "scenario_seed": scenario_seeds[0] if scenario_seeds else None,
                "scenario_id": "single" if scenario_seeds else None,
            }
        )

    if args.output_root:
        output_root = Path(args.output_root).resolve()
    else:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_root = repo_root / ".dist" / "llm_compare" / ts
    output_root.mkdir(parents=True, exist_ok=True)

    run_profile: dict[str, Any] = {
        "profile_name": profile_name,
        "strict_mode": profile_name == "strict",
        "strict_baseline": {
            "max_eps": STRICT_BASELINE_MAX_EPS,
            "episode_length": STRICT_BASELINE_EPISODE_LENGTH,
        },
        "effective": {
            "max_eps": max_eps,
            "episode_length": episode_length,
            "models": [name for name, _ in models],
        },
        "matrix_mode": args.matrix,
        "matrix_cases": matrix_cases,
    }
    (output_root / "run_profile.json").write_text(json.dumps(run_profile, indent=2), encoding="utf-8")

    print(f"[INFO] Repo root: {repo_root}")
    print(f"[INFO] Evaluation workspace: {eval_workspace}")
    print(f"[INFO] Submission path: {submission_path}")
    print(f"[INFO] Output root: {output_root}")
    print(f"[INFO] Profile: {profile_name}")
    print(f"[INFO] Matrix mode: {args.matrix} (cases={len(matrix_cases)})")
    print(f"[INFO] Effective settings: max_eps={max_eps}, episode_length={episode_length}, heartbeat_sec={args.heartbeat_sec}, timeout_sec={args.timeout_sec}")

    results: list[ModelRunResult] = []
    for model_name, model_cfg in models:
        print(f"[INFO] Running model: {model_name} ({model_cfg})")
        for case in matrix_cases:
            case_id = str(case["case_id"])
            run_dir = output_root / model_name / case_id
            print(
                f"[INFO] Running case {case_id} | red={case.get('red_variant')} "
                f"| scenario_seed={case.get('scenario_seed')}"
            )
            result = _run_single_model(
                repo_root=repo_root,
                eval_workspace=eval_workspace,
                submission_path=submission_path,
                model_name=model_name,
                model_cfg=model_cfg,
                run_output_dir=run_dir,
                max_eps=max_eps,
                episode_length=episode_length,
                heartbeat_sec=args.heartbeat_sec,
                timeout_sec=args.timeout_sec,
                wandb_mode=args.wandb_mode,
                wandb_entity=args.wandb_entity,
                run_profile=run_profile,
                case_id=case_id,
                red_variant=case.get("red_variant"),
                scenario_seed=case.get("scenario_seed"),
                scenario_id=case.get("scenario_id"),
            )
            results.append(result)
            print(
                f"[INFO] Completed {model_name}/{case_id} | return_code={result.return_code} "
                f"| mean_reward={result.reward_mean} | elapsed={result.elapsed}"
            )

    _write_comparison(output_root, results, run_profile)
    print(f"[INFO] Comparison report: {output_root / 'comparison.md'}")
    print(f"[INFO] Comparison data: {output_root / 'comparison.json'}")

    if any(r.return_code != 0 for r in results):
        print("[WARN] One or more model runs failed. Check per-model stderr.log files.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
