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
from typing import Any


@dataclass
class ModelRunResult:
    name: str
    config_path: str
    output_dir: str
    return_code: int
    summary: dict[str, Any] | None
    elapsed: str | None
    reward_mean: float | None
    reward_stdev: float | None


def _resolve_defaults() -> tuple[Path, Path, Path, Path, list[str]]:
    repo_root = Path(__file__).resolve().parents[3]
    eval_workspace = repo_root / "cage-challenge-4"
    submission_path = eval_workspace / "CybORG" / "Evaluation" / "llamagym"
    model_config_dir = repo_root / "CybORG" / "Agents" / "LLMAgents" / "config" / "model"
    default_models = ["deepseek-r1-1.5b", "gemma4-e4b"]
    return repo_root, eval_workspace, submission_path, model_config_dir, default_models


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


def _run_single_model(
    repo_root: Path,
    eval_workspace: Path,
    submission_path: Path,
    model_name: str,
    model_cfg: Path,
    output_root: Path,
    max_eps: int,
    episode_length: int,
    heartbeat_sec: int,
    timeout_sec: int,
    wandb_mode: str,
    wandb_entity: str | None,
) -> ModelRunResult:
    model_out_dir = output_root / model_name
    model_out_dir.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["CAGE4_MODEL_CONFIG"] = str(model_cfg)
    env["CAGE_EPISODE_LENGTH"] = str(episode_length)
    env["CAGE4_DEBUG_MODE"] = "false"

    cmd = [
        sys.executable,
        "-m",
        "CybORG.Evaluation.evaluation",
        "--max-eps",
        str(max_eps),
        str(submission_path),
        str(model_out_dir),
    ]
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

    stdout_path = model_out_dir / "stdout.log"
    stderr_path = model_out_dir / "stderr.log"

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
                        err_f.write(line)
                        err_f.flush()
                        print(f"[{model_name}][ERR] {line}", end="")
                break

    t_out.join(timeout=1)
    t_err.join(timeout=1)

    return_code = proc.returncode if proc.returncode is not None else 1
    if timed_out and return_code == 0:
        return_code = 124

    summary_path = model_out_dir / "summary.json"
    summary = None
    elapsed = None
    reward_mean = None
    reward_stdev = None

    if summary_path.exists():
        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            elapsed = (summary.get("time") or {}).get("elapsed")
            reward = summary.get("reward") or {}
            reward_mean = reward.get("mean")
            reward_stdev = reward.get("stdev")
        except Exception:
            summary = None

    return ModelRunResult(
        name=model_name,
        config_path=str(model_cfg),
        output_dir=str(model_out_dir),
        return_code=return_code,
        summary=summary,
        elapsed=elapsed,
        reward_mean=reward_mean,
        reward_stdev=reward_stdev,
    )


def _write_comparison(output_root: Path, results: list[ModelRunResult]) -> None:
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "models": [
            {
                "name": r.name,
                "config_path": r.config_path,
                "output_dir": r.output_dir,
                "return_code": r.return_code,
                "elapsed": r.elapsed,
                "reward_mean": r.reward_mean,
                "reward_stdev": r.reward_stdev,
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
        "",
        "| Model | Return Code | Mean Reward | Reward StdDev | Elapsed | Config |",
        "|---|---:|---:|---:|---|---|",
    ]
    for r in results:
        mean_txt = "n/a" if r.reward_mean is None else f"{r.reward_mean:.4f}"
        std_txt = "n/a" if r.reward_stdev is None else f"{r.reward_stdev:.4f}"
        elapsed_txt = r.elapsed or "n/a"
        lines.append(
            f"| {r.name} | {r.return_code} | {mean_txt} | {std_txt} | {elapsed_txt} | {r.config_path} |"
        )

    comparison_md = output_root / "comparison.md"
    comparison_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run LLM model comparison for CybORG llamagym submission.")
    parser.add_argument("--max-eps", type=int, default=2, help="Max episodes per model run.")
    parser.add_argument("--quick", action="store_true", help="Quick first run: sets max-eps=2 and episode-length=5 unless overridden.")
    parser.add_argument("--episode-length", type=int, default=None, help="Episode length override (default: 500, or 5 in --quick mode).")
    parser.add_argument("--heartbeat-sec", type=int, default=10, help="Heartbeat interval in seconds for live progress feedback.")
    parser.add_argument("--timeout-sec", type=int, default=0, help="Optional timeout per model run (0 disables timeout).")
    parser.add_argument("--wandb-mode", type=str, default="offline", choices=["offline", "online"], help="Weights & Biases mode.")
    parser.add_argument("--wandb-entity", type=str, default=None, help="Optional wandb entity.")
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

    max_eps = 2 if args.quick else args.max_eps
    if max_eps < 2:
        print("[INFO] For compatibility with evaluation.py statistics, forcing max_eps=2.")
        max_eps = 2
    episode_length = args.episode_length if args.episode_length is not None else (5 if args.quick else 500)

    if args.output_root:
        output_root = Path(args.output_root).resolve()
    else:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_root = repo_root / ".dist" / "llm_compare" / ts
    output_root.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Repo root: {repo_root}")
    print(f"[INFO] Evaluation workspace: {eval_workspace}")
    print(f"[INFO] Submission path: {submission_path}")
    print(f"[INFO] Output root: {output_root}")
    print(f"[INFO] Effective settings: max_eps={max_eps}, episode_length={episode_length}, heartbeat_sec={args.heartbeat_sec}, timeout_sec={args.timeout_sec}")

    results: list[ModelRunResult] = []
    for model_name, model_cfg in models:
        print(f"[INFO] Running model: {model_name} ({model_cfg})")
        result = _run_single_model(
            repo_root=repo_root,
            eval_workspace=eval_workspace,
            submission_path=submission_path,
            model_name=model_name,
            model_cfg=model_cfg,
            output_root=output_root,
            max_eps=max_eps,
            episode_length=episode_length,
            heartbeat_sec=args.heartbeat_sec,
            timeout_sec=args.timeout_sec,
            wandb_mode=args.wandb_mode,
            wandb_entity=args.wandb_entity,
        )
        results.append(result)
        print(
            f"[INFO] Completed {model_name} | return_code={result.return_code} "
            f"| mean_reward={result.reward_mean} | elapsed={result.elapsed}"
        )

    _write_comparison(output_root, results)
    print(f"[INFO] Comparison report: {output_root / 'comparison.md'}")
    print(f"[INFO] Comparison data: {output_root / 'comparison.json'}")

    if any(r.return_code != 0 for r in results):
        print("[WARN] One or more model runs failed. Check per-model stderr.log files.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
