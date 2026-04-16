#!/usr/bin/env python3
"""
Matplotlib visualization of CAGE Challenge 4 Parity Comparison Results
Comparing baseline, UCSC hybrid, RL expert, and local implementations
SEPARATE DIAGRAMS VERSION - Each visualization in its own figure
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle
from pathlib import Path

# Set style
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.size'] = 11
plt.rcParams['axes.grid'] = True
plt.rcParams['grid.alpha'] = 0.3

# Output directory for generated figures
OUTPUT_DIR = Path(__file__).resolve().parent / "assets"
OUTPUT_DIR.mkdir(exist_ok=True)

# Data from parity comparison table
models = [
    'Baseline\n(All-LLM)',
    'UCSC Hybrid\n(LLM + RL)',
    'KEEP RL Expert\n(Pure RL)',
    'Ours: Enhanced\nHybrid (Qwen)',
    'Ours: Enhanced\nHybrid (DeepSeek)'
]

rewards_mean = [-2547.2, -1600, -493.0, -866.5, -477.5]
rewards_std = [498.8, 700, 95.9, 341.53, 116.67]
cv_values = [abs(std / mean) for mean, std in zip(rewards_mean, rewards_std)]

colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']
edge_colors = ['#C92A2A', '#0A8080', '#0D6BA3', '#DD6D3D', '#4A9B7F']

# ============================================================================
# 1. Mean Reward Comparison with Error Bars
# ============================================================================
fig1, ax1 = plt.subplots(figsize=(12, 7))
x_pos = np.arange(len(models))
bars = ax1.bar(x_pos, rewards_mean, yerr=rewards_std, capsize=10, 
               color=colors, edgecolor=edge_colors, linewidth=2.5, alpha=0.8, 
               error_kw={'elinewidth': 2.5, 'capthick': 3})

ax1.set_ylabel('Mean Reward (μ)', fontsize=14, fontweight='bold')
ax1.set_xlabel('Agent Configuration', fontsize=14, fontweight='bold')
ax1.set_title('Mean Reward Comparison with Standard Deviation\nCAGE Challenge 4 (1 LLM + 4 RL, 2×500 Steps)', 
              fontsize=15, fontweight='bold', pad=20)
ax1.set_xticks(x_pos)
ax1.set_xticklabels(models, fontsize=12)
ax1.axhline(y=0, color='black', linestyle='-', linewidth=0.8, alpha=0.3)
ax1.grid(axis='y', alpha=0.4, linewidth=0.8)

# Add value labels on bars
for i, (bar, mean, std) in enumerate(zip(bars, rewards_mean, rewards_std)):
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height,
             f'{mean:.1f}\n±{std:.1f}',
             ha='center', va='bottom' if height > 0 else 'top', 
             fontsize=11, fontweight='bold')

plt.tight_layout()
out_file = OUTPUT_DIR / '01_mean_reward_comparison.png'
plt.savefig(out_file, dpi=300, bbox_inches='tight')
print(f"✓ Saved: {out_file}")
plt.close()

# ============================================================================
# 2. Improvement Percentage (vs Baseline)
# ============================================================================
fig2, ax2 = plt.subplots(figsize=(12, 7))
improvement_vals = []
improvement_labels = []
improvement_colors_filt = []
baseline_reward = -2547.2

for i, (model, reward) in enumerate(zip(models, rewards_mean)):
    if i > 0:
        imp = ((baseline_reward - reward) / abs(baseline_reward)) * 100
        improvement_vals.append(imp)
        improvement_labels.append(model)
        improvement_colors_filt.append(colors[i])

x_pos_imp = np.arange(len(improvement_vals))
bars_imp = ax2.bar(x_pos_imp, improvement_vals, color=improvement_colors_filt, 
                   edgecolor=edge_colors[1:], linewidth=2.5, alpha=0.8, width=0.6)

ax2.set_ylabel('Improvement vs Baseline (%)', fontsize=14, fontweight='bold')
ax2.set_xlabel('Agent Configuration', fontsize=14, fontweight='bold')
ax2.set_title('Performance Improvement vs GPT-4o Mini Baseline\nCAGE Challenge 4 Parity Comparison', 
              fontsize=15, fontweight='bold', pad=20)
ax2.set_xticks(x_pos_imp)
ax2.set_xticklabels(improvement_labels, fontsize=12)
ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.8, alpha=0.3)
ax2.grid(axis='y', alpha=0.4, linewidth=0.8)
ax2.set_ylim(0, max(improvement_vals) * 1.15)

# Add percentage labels
for bar, val in zip(bars_imp, improvement_vals):
    height = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., height,
             f'+{val:.1f}%',
             ha='center', va='bottom', fontsize=12, fontweight='bold', color='darkgreen')

plt.tight_layout()
out_file = OUTPUT_DIR / '02_improvement_percentage.png'
plt.savefig(out_file, dpi=300, bbox_inches='tight')
print(f"✓ Saved: {out_file}")
plt.close()

# ============================================================================
# 3. Standard Deviation Comparison
# ============================================================================
fig3, ax3 = plt.subplots(figsize=(12, 7))
bars_std = ax3.bar(x_pos, rewards_std, color=colors, edgecolor=edge_colors, 
                   linewidth=2.5, alpha=0.8)

ax3.set_ylabel('Standard Deviation (σ)', fontsize=14, fontweight='bold')
ax3.set_xlabel('Agent Configuration', fontsize=14, fontweight='bold')
ax3.set_title('Reward Variability Across Episodes\nHigher Variability = Less Stable Performance', 
              fontsize=15, fontweight='bold', pad=20)
ax3.set_xticks(x_pos)
ax3.set_xticklabels(models, fontsize=12)
ax3.grid(axis='y', alpha=0.4, linewidth=0.8)
ax3.set_ylim(0, max(rewards_std) * 1.1)

# Add value labels
for bar, std in zip(bars_std, rewards_std):
    height = bar.get_height()
    ax3.text(bar.get_x() + bar.get_width()/2., height,
             f'{std:.1f}',
             ha='center', va='bottom', fontsize=11, fontweight='bold')

plt.tight_layout()
out_file = OUTPUT_DIR / '03_standard_deviation.png'
plt.savefig(out_file, dpi=300, bbox_inches='tight')
print(f"✓ Saved: {out_file}")
plt.close()

# ============================================================================
# 4. Coefficient of Variation (Stability)
# ============================================================================
fig4, ax4 = plt.subplots(figsize=(12, 7))
bars_cv = ax4.bar(x_pos, cv_values, color=colors, edgecolor=edge_colors, 
                  linewidth=2.5, alpha=0.8)

ax4.set_ylabel('Coefficient of Variation (σ/|μ|)', fontsize=14, fontweight='bold')
ax4.set_xlabel('Agent Configuration', fontsize=14, fontweight='bold')
ax4.set_title('Agent Performance Stability (Lower CV = More Consistent)\nCAGE Challenge 4', 
              fontsize=15, fontweight='bold', pad=20)
ax4.set_xticks(x_pos)
ax4.set_xticklabels(models, fontsize=12)
ax4.grid(axis='y', alpha=0.4, linewidth=0.8)
ax4.set_ylim(0, max(cv_values) * 1.1)

# Add value labels
for bar, cv in zip(bars_cv, cv_values):
    height = bar.get_height()
    ax4.text(bar.get_x() + bar.get_width()/2., height,
             f'{cv:.3f}',
             ha='center', va='bottom', fontsize=11, fontweight='bold')

plt.tight_layout()
out_file = OUTPUT_DIR / '04_stability_coefficient.png'
plt.savefig(out_file, dpi=300, bbox_inches='tight')
print(f"✓ Saved: {out_file}")
plt.close()

# ============================================================================
# 5. Confidence Interval Visualization
# ============================================================================
fig5, ax5 = plt.subplots(figsize=(14, 8))
y_positions = np.arange(len(models))

for i, (model, mean, std) in enumerate(zip(models, rewards_mean, rewards_std)):
    ci_lower = mean - 2*std
    ci_upper = mean + 2*std
    
    # Draw confidence interval line
    ax5.plot([ci_lower, ci_upper], [i, i], 'o-', linewidth=4, 
             color=colors[i], markersize=10, markeredgecolor=edge_colors[i], 
             markeredgewidth=2.5, alpha=0.85, label=model.replace('\n', ' '))
    
    # Mark mean
    ax5.plot(mean, i, 'D', markersize=12, color=colors[i], 
             markeredgecolor=edge_colors[i], markeredgewidth=2.5, zorder=5)
    
    # Add text annotations
    ax5.text(ci_lower - 300, i, f'{ci_lower:.0f}', fontsize=10, 
             ha='right', va='center', fontweight='bold')
    ax5.text(ci_upper + 300, i, f'{ci_upper:.0f}', fontsize=10, 
             ha='left', va='center', fontweight='bold')

ax5.set_yticks(y_positions)
ax5.set_yticklabels(models, fontsize=12)
ax5.set_xlabel('Reward Value (μ)', fontsize=14, fontweight='bold')
ax5.set_title('95% Confidence Intervals (Mean ± 2σ)\nEstimated Range of Expected Performance', 
              fontsize=15, fontweight='bold', pad=20)
ax5.axvline(x=0, color='black', linestyle='--', linewidth=1.5, alpha=0.5)
ax5.grid(axis='x', alpha=0.4, linewidth=0.8)
ax5.set_xlim(-3500, 500)

plt.tight_layout()
out_file = OUTPUT_DIR / '05_confidence_intervals.png'
plt.savefig(out_file, dpi=300, bbox_inches='tight')
print(f"✓ Saved: {out_file}")
plt.close()

# ============================================================================
# 6. Summary Statistics Table
# ============================================================================
fig6, ax6 = plt.subplots(figsize=(14, 8))
ax6.axis('off')

# Create summary table
summary_data = []
for i, model in enumerate(models):
    summary_data.append([
        model.replace('\n', ' '),
        f"{rewards_mean[i]:.1f}",
        f"{rewards_std[i]:.1f}",
        f"{cv_values[i]:.4f}"
    ])

table = ax6.table(cellText=summary_data,
                  colLabels=['Configuration', 'Mean Reward (μ)', 'Std Dev (σ)', 'Stability (CV)'],
                  cellLoc='center',
                  loc='center',
                  colWidths=[0.30, 0.25, 0.25, 0.20])

table.auto_set_font_size(False)
table.set_fontsize(12)
table.scale(1, 3)

# Style header
for i in range(4):
    table[(0, i)].set_facecolor('#2c3e50')
    table[(0, i)].set_text_props(weight='bold', color='white', fontsize=13)

# Style rows with alternating colors
for i in range(1, len(summary_data) + 1):
    for j in range(4):
        if i % 2 == 0:
            table[(i, j)].set_facecolor('#ecf0f1')
        else:
            table[(i, j)].set_facecolor('white')
        table[(i, j)].set_text_props(fontsize=12, fontweight='bold')

# Add a subtle border
for key, cell in table.get_celld().items():
    cell.set_linewidth(1.5)
    cell.set_edgecolor('#34495e')

ax6.text(0.5, 0.95, 'Summary Statistics: CAGE Challenge 4 Parity Comparison',
         ha='center', va='top', fontsize=16, fontweight='bold', 
         transform=ax6.transAxes)

plt.tight_layout()
out_file = OUTPUT_DIR / '06_summary_statistics.png'
plt.savefig(out_file, dpi=300, bbox_inches='tight')
print(f"✓ Saved: {out_file}")
plt.close()

# ============================================================================
# 7. Paper vs Our Results Comparison
# ============================================================================
fig7, ax7 = plt.subplots(figsize=(13, 8))

paper_models = ['GPT-4o Mini\n(Baseline)', 'UCSC Hybrid\n(LLM+RL)', 'KEEP RL\n(Pure RL)']
paper_rewards = [-2547.2, -1600, -493.0]
paper_std = [498.8, 700, 95.9]
paper_colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']

our_models = ['Qwen2.5-7b\n(Ours)', 'DeepSeek-r1-1.5b\n(Ours)']
our_rewards = [-866.5, -477.5]
our_std = [341.53, 116.67]
our_colors = ['#FFA07A', '#98D8C8']

x_paper = np.arange(len(paper_models))
x_our = np.arange(len(our_models)) + len(paper_models) + 0.8

all_x = list(x_paper) + list(x_our)
all_rewards = paper_rewards + our_rewards
all_std = paper_std + our_std
all_colors = paper_colors + our_colors
all_labels = paper_models + our_models

bars = ax7.bar(all_x, all_rewards, yerr=all_std, capsize=10,
               color=all_colors, edgecolor=['#C92A2A', '#0A8080', '#0D6BA3', '#DD6D3D', '#4A9B7F'],
               linewidth=2.5, alpha=0.85, error_kw={'elinewidth': 2.5, 'capthick': 3})

ax7.set_ylabel('Mean Reward (μ)', fontsize=14, fontweight='bold')
ax7.set_xlabel('Agent Configuration', fontsize=14, fontweight='bold')
ax7.set_title('Paper Results vs Our Implementations\nCAGE Challenge 4 Parity Comparison', 
              fontsize=15, fontweight='bold', pad=20)
ax7.set_xticks(all_x)
ax7.set_xticklabels(all_labels, fontsize=12)
ax7.axhline(y=0, color='black', linestyle='-', linewidth=0.8, alpha=0.3)
ax7.grid(axis='y', alpha=0.4, linewidth=0.8)

# Add divider line
ax7.axvline(x=(len(paper_models)-0.5) + 0.4, color='black', linestyle='--', 
            linewidth=2.5, alpha=0.6)

# Add section labels
ax7.text(1, ax7.get_ylim()[1]*0.92, 'Paper Results', fontsize=13, 
         fontweight='bold', ha='center', 
         bbox=dict(boxstyle='round,pad=0.6', facecolor='wheat', alpha=0.7, edgecolor='black', linewidth=2))
ax7.text(3.8, ax7.get_ylim()[1]*0.92, 'Our Results', fontsize=13, 
         fontweight='bold', ha='center',
         bbox=dict(boxstyle='round,pad=0.6', facecolor='lightblue', alpha=0.7, edgecolor='black', linewidth=2))

# Add value labels
for i, (bar, mean, std) in enumerate(zip(bars, all_rewards, all_std)):
    height = bar.get_height()
    ax7.text(bar.get_x() + bar.get_width()/2., height,
             f'{mean:.1f}\n±{std:.1f}',
             ha='center', va='bottom' if height > 0 else 'top', 
             fontsize=10, fontweight='bold')

plt.tight_layout()
out_file = OUTPUT_DIR / '07_paper_vs_ours.png'
plt.savefig(out_file, dpi=300, bbox_inches='tight')
print(f"✓ Saved: {out_file}")
plt.close()

# ============================================================================
# 8. Relative Performance Improvement
# ============================================================================
fig8, ax8 = plt.subplots(figsize=(13, 8))

baseline = -2547.2
improvements_vs_baseline = []
model_names = []

all_rewards_combined = paper_rewards + our_rewards
for reward in all_rewards_combined:
    imp = ((baseline - reward) / abs(baseline)) * 100
    improvements_vs_baseline.append(imp)
    
for model in paper_models + our_models:
    model_names.append(model)

colors_improvement = ['#bdc3c7', '#bdc3c7', '#bdc3c7', '#FFA07A', '#98D8C8']
bars2 = ax8.barh(model_names, improvements_vs_baseline, 
                 color=colors_improvement, edgecolor=['#7f8c8d', '#7f8c8d', '#7f8c8d', '#DD6D3D', '#4A9B7F'],
                 linewidth=2.5, alpha=0.85, height=0.6)

ax8.set_xlabel('Improvement vs Baseline (%)', fontsize=14, fontweight='bold')
ax8.set_ylabel('Agent Configuration', fontsize=14, fontweight='bold')
ax8.set_title('Relative Performance vs GPT-4o Mini Baseline\nHigher % = Better Performance', 
              fontsize=15, fontweight='bold', pad=20)
ax8.grid(axis='x', alpha=0.4, linewidth=0.8)

max_val = max(improvements_vs_baseline) if improvements_vs_baseline else 100
ax8.set_xlim(0, max(max_val * 1.15, 85))

# Add value labels
for bar, val in zip(bars2, improvements_vs_baseline):
    width = bar.get_width()
    ax8.text(width + 2, bar.get_y() + bar.get_height()/2.,
             f'+{val:.1f}%',
             ha='left', va='center', fontsize=12, fontweight='bold', color='darkgreen')

plt.tight_layout()
out_file = OUTPUT_DIR / '08_relative_improvement.png'
plt.savefig(out_file, dpi=300, bbox_inches='tight')
print(f"✓ Saved: {out_file}")
plt.close()


print("\n" + "="*70)
print("MATPLOTLIB VISUALIZATION COMPLETE - SEPARATE DIAGRAMS")
print("="*70)

print("\nGenerated 8 separate visualization files:")
print("\n1. 01_mean_reward_comparison.png")
print("   Main comparison of all agent configurations with error bars")

print("\n2. 02_improvement_percentage.png")
print("   Performance improvement percentages vs baseline")

print("\n3. 03_standard_deviation.png")
print("   Reward variability across episodes for each configuration")

print("\n4. 04_stability_coefficient.png")
print("   Coefficient of variation (CV) - consistency metric")

print("\n5. 05_confidence_intervals.png")
print("   95% confidence interval ranges (Mean ± 2σ)")

print("\n6. 06_summary_statistics.png")
print("   Table with all key metrics for easy reference")

print("\n7. 07_paper_vs_ours.png")
print("   Side-by-side comparison: Paper baselines + Our implementations")

print("\n8. 08_relative_improvement.png")
print("   Horizontal bar chart of improvement percentages")

print("\n" + "="*70)
print("KEY FINDINGS:")
print("="*70)
print(f"\nBaseline (GPT-4o Mini):        μ = -2547.2  ±  498.8   (CV = 0.196)")
print(f"UCSC Hybrid (LLM+RL):          μ = -1600    ±  ~700    (+37.1%, CV = 0.438)")
print(f"KEEP RL Expert (Pure RL):      μ = -493.0   ±  95.9    (+80.6%, CV = 0.195)")
print(f"Ours: Qwen2.5-7b Hybrid:       μ = -866.5   ±  341.53  (+65.9%, CV = 0.394)")
print(f"Ours: DeepSeek-r1-1.5b Hybrid: μ = -477.5   ±  116.67  (+81.3%, CV = 0.244)")

print("\nPerformance Rankings:")
print("  🥇 Best Reward:    DeepSeek-r1-1.5b (-477.5)")
print("  🥈 Second:         KEEP RL Expert (-493.0)")
print("  🥉 Third:          Qwen2.5-7b (-866.5)")

print("\nStability Rankings (Lower CV = More Consistent):")
print("  🥇 Most Stable:    KEEP RL Expert (CV = 0.195) / Baseline (CV = 0.196)")
print("  🥈 Second:         DeepSeek-r1-1.5b (CV = 0.244)")
print("  🥉 Third:          Qwen2.5-7b (CV = 0.394)")

print("\n" + "="*70)
print(f"All visualizations are ready in: {OUTPUT_DIR}")
print("="*70 + "\n")
