#!/usr/bin/env python3
"""Create a single graph showing total hallucinations vs repaired hallucinations.

The figure uses one grouped bar chart with one pair of bars per model:
total hallucinations and repaired hallucinations. The percentage of
successful fixes is annotated above the repaired bar.
"""

from pathlib import Path
import json

import matplotlib.pyplot as plt
import numpy as np

OUTPUT_DIR = Path(__file__).resolve().parent / "assets"
OUTPUT_DIR.mkdir(exist_ok=True)

QWEN_SUMMARY = Path(__file__).resolve().parents[1] / "results" / "cybermonics_strict_comparison_qwen" / "results" / "summary.json"
DEEPSEEK_SUMMARY = Path(__file__).resolve().parents[1] / "results" / "cybermonics_strict_comparison_deepseek" / "results" / "summary.json"
OUTPUT_FILE = OUTPUT_DIR / "09_hallucinations_vs_repairs.png"


def load_summary(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


qwen = load_summary(QWEN_SUMMARY)["hallucination"]
deepseek = load_summary(DEEPSEEK_SUMMARY)["hallucination"]

models = ["DeepSeek-r1-1.5b", "Qwen-2.5"]
total_hallucinations = [deepseek["total_hallucination_count"], qwen["total_hallucination_count"]]
repaired_hallucinations = [deepseek["repair_success_count"], qwen["repair_success_count"]]
repair_success_rates = [
    deepseek["repair_success_count"] / deepseek["repair_attempt_count"] * 100.0,
    qwen["repair_success_count"] / qwen["repair_attempt_count"] * 100.0,
]

plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
fig, ax = plt.subplots(figsize=(11, 7))

x = np.arange(len(models))
bar_width = 0.34
edge_color = "#2F2F2F"

bars_total = ax.bar(
    x - bar_width / 2,
    total_hallucinations,
    width=bar_width,
    color="#E74C3C",
    edgecolor=edge_color,
    linewidth=1.2,
    alpha=0.9,
    label="Total hallucinations",
)

bars_repaired = ax.bar(
    x + bar_width / 2,
    repaired_hallucinations,
    width=bar_width,
    color="#2ECC71",
    edgecolor=edge_color,
    linewidth=1.2,
    alpha=0.9,
    label="Repaired hallucinations",
)

for bar, total in zip(bars_total, total_hallucinations):
    height = bar.get_height()
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        height,
        f"{int(height)}",
        ha="center",
        va="bottom",
        fontsize=11,
        fontweight="bold",
    )

for bar, rate in zip(bars_repaired, repair_success_rates):
    height = bar.get_height()
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        height,
        f"{rate:.1f}%",
        ha="center",
        va="bottom",
        fontsize=11,
        fontweight="bold",
    )

ax.set_title(
    "Total Hallucinations vs Repaired Hallucinations\nSuccessful fix rate shown above repaired bars",
    fontsize=16,
    fontweight="bold",
    pad=18,
)
ax.set_ylabel("Count", fontsize=13, fontweight="bold")
ax.set_xticks(x)
ax.set_xticklabels(models, fontsize=12)
ax.grid(axis="y", alpha=0.35)
ax.legend(fontsize=11, loc="upper right")

ax.set_ylim(0, max(total_hallucinations) * 1.25)
ax.text(
    0.01,
    0.98,
    "Numbers on the repaired bars are successful-fix percentages; the bars themselves are counts.",
    transform=ax.transAxes,
    ha="left",
    va="top",
    fontsize=10,
    color="#444444",
)

fig.tight_layout()
fig.savefig(OUTPUT_FILE, dpi=300, bbox_inches="tight")
print(f"Saved single graph: {OUTPUT_FILE}")
