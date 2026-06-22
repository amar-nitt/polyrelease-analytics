# =============================================================
# FILE:    scripts/07_eda.py
# PROJECT: PolyRelease Analytics
# PHASE:   4 — Exploratory Data Analysis
# =============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns
import os

# ── Setup ────────────────────────────────────────────────────────
os.makedirs("charts", exist_ok=True)

df_master  = pd.read_csv("data/master_analytical.csv")
df_summary = pd.read_csv("data/formulation_summary.csv")

# Consistent polymer colours used across ALL charts in this project.
# Defining once here keeps every chart visually coherent.
POLYMER_COLOURS = {
    'PVA':        '#2196F3',    # blue
    'Chitosan':   '#4CAF50',    # green
    'PLGA 50:50': '#FF9800',    # orange
    'HPMC K100':  '#9C27B0',    # purple
}

# Ordered from highest to lowest release — used to order chart axes.
POLYMER_ORDER = ['PVA', 'Chitosan', 'PLGA 50:50', 'HPMC K100']

# Standard matplotlib style settings for a clean, professional look.
plt.rcParams.update({
    'font.family':       'sans-serif',
    'axes.spines.top':   False,
    'axes.spines.right': False,
    'axes.grid':         True,
    'grid.alpha':        0.3,
    'grid.linestyle':    '--',
    'figure.dpi':        150,
})

print("=" * 62)
print("  Phase 4 — Exploratory Data Analysis")
print("=" * 62)
print(f"✅ Loaded master data:  {df_master.shape[0]} rows × {df_master.shape[1]} columns")
print(f"✅ Loaded summary data: {df_summary.shape[0]} rows × {df_summary.shape[1]} columns")

# =============================================================
# CHART 1 — Release Profiles by Polymer (Line Chart)
# Question: How does each polymer release drug over time?
# =============================================================

print("\n📊 Building Chart 1: Release profiles over time...")

fig, ax = plt.subplots(figsize=(10, 6))

for polymer in POLYMER_ORDER:
    data         = df_master[df_master['polymer_name'] == polymer]
    avg_by_time  = (
        data.groupby('time_point_hours')['cumulative_release_pct']
        .mean()
        .reset_index()
    )

    ax.plot(
        avg_by_time['time_point_hours'],
        avg_by_time['cumulative_release_pct'],
        marker    = 'o',
        linewidth = 2.5,
        markersize= 7,
        color     = POLYMER_COLOURS[polymer],
        label     = polymer,
        zorder    = 3,
    )

    # Annotate the final 48h value on each line
    final_val = avg_by_time[avg_by_time['time_point_hours'] == 48][
        'cumulative_release_pct'].values[0]
    ax.annotate(
        f"{final_val:.1f}%",
        xy     = (48, final_val),
        xytext = (4, 0),
        textcoords = 'offset points',
        fontsize   = 10,
        fontweight = 'bold',
        color      = POLYMER_COLOURS[polymer],
        va         = 'center',
    )

# Chart formatting
ax.set_xlabel("Time (hours)", fontsize=12, labelpad=8)
ax.set_ylabel("Cumulative Drug Release (%)", fontsize=12, labelpad=8)
ax.set_title(
    "Average Drug Release Profiles by Polymer Type\n"
    "Mean across all valid batches   |   pH 6.8   |   n=19 batches",
    fontsize=13, pad=12
)
ax.set_xticks([0, 1, 2, 4, 8, 12, 24, 48])
ax.set_xticklabels(['0h', '1h', '2h', '4h', '8h', '12h', '24h', '48h'])
ax.set_ylim(0, 105)
ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=100, decimals=0))
ax.legend(
    title      = "Polymer",
    loc        = 'upper left',
    fontsize   = 10,
    title_fontsize = 10,
)

# Shade the 0–8h "early burst" window as a visual reference region
ax.axvspan(0, 8, alpha=0.06, color='gray', label='_nolegend_')
ax.text(4, 3, 'Early burst\nwindow', ha='center',
        fontsize=8, color='gray', style='italic')

plt.tight_layout()
plt.savefig("charts/chart_01_release_profiles.png", bbox_inches='tight')
plt.show()
print("✅ Chart 1 saved: charts/chart_01_release_profiles.png")

# Quick data check: confirm ordering of final values
print("\n   48h release values used in chart:")
for polymer in POLYMER_ORDER:
    data       = df_master[
        (df_master['polymer_name'] == polymer) &
        (df_master['time_point_hours'] == 48)
    ]
    avg = data['cumulative_release_pct'].mean()
    print(f"   {polymer:<16}  {avg:.1f}%")

print("\n" + "─" * 62)
print("  ✅ Task 1 complete. Confirm chart opened, then Task 2.")
print("─" * 62)

# =============================================================
# CHART 2 — Polymer Performance Comparison (Bar + Error Bars)
# Question: Which polymer performs best at 48h, and how consistent?
# =============================================================

print("\n📊 Building Chart 2: Polymer performance comparison...")

# ── Prepare 48h statistics per polymer ───────────────────────────
df_48h = df_master[df_master['time_point_hours'] == 48].copy()

polymer_stats = (
    df_48h
    .groupby('polymer_name')['cumulative_release_pct']
    .agg(mean='mean', std='std', count='count')
    .round(2)
    .reset_index()
)
polymer_stats['cv_pct'] = (
    polymer_stats['std'] / polymer_stats['mean'] * 100
).round(1)

# Reorder to match consistent POLYMER_ORDER across all charts
polymer_stats['polymer_name'] = pd.Categorical(
    polymer_stats['polymer_name'],
    categories=POLYMER_ORDER, ordered=True
)
polymer_stats = polymer_stats.sort_values('polymer_name').reset_index(drop=True)

# ── Draw chart ────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(9, 6))

ax.bar(
    polymer_stats['polymer_name'],
    polymer_stats['mean'],
    yerr     = polymer_stats['std'],
    capsize  = 6,
    color    = [POLYMER_COLOURS[p] for p in polymer_stats['polymer_name']],
    alpha    = 0.85,
    error_kw = {'elinewidth': 1.5, 'ecolor': 'black', 'capthick': 1.5},
    zorder   = 3,
    width    = 0.55,
)

# Annotate each bar with mean value (above) and CV + n (inside)
for i, row in polymer_stats.iterrows():
    # Value label above error bar
    ax.text(
        i, row['mean'] + row['std'] + 2.0,
        f"{row['mean']:.1f}%",
        ha='center', va='bottom',
        fontsize=11, fontweight='bold',
        color=POLYMER_COLOURS[row['polymer_name']],
    )
    # CV and sample size inside bar
    ax.text(
        i, row['mean'] / 2,
        f"CV: {row['cv_pct']}%\nn = {int(row['count'])}",
        ha='center', va='center',
        fontsize=9, color='white', fontweight='bold',
    )

# Reference line: overall mean across all polymers
overall_mean = df_48h['cumulative_release_pct'].mean()
ax.axhline(
    overall_mean,
    color='gray', linestyle='--', linewidth=1.2, alpha=0.7
)
ax.text(
    3.45, overall_mean + 1.5,
    f"Overall mean: {overall_mean:.1f}%",
    fontsize=8, color='gray', ha='right'
)

# Chart formatting
ax.set_xlabel("Polymer Type", fontsize=12, labelpad=8)
ax.set_ylabel("Mean Cumulative Release at 48h (%)", fontsize=12, labelpad=8)
ax.set_title(
    "Polymer Performance Comparison at 48 Hours\n"
    "Error bars = ±1 SD   |   CV = Coefficient of Variation   |   "
    "Valid batches only",
    fontsize=13, pad=12
)
ax.set_ylim(0, 110)
ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=100, decimals=0))
ax.tick_params(axis='x', labelsize=11)

plt.tight_layout()
plt.savefig("charts/chart_02_polymer_comparison.png", bbox_inches='tight')
plt.show()

print("✅ Chart 2 saved: charts/chart_02_polymer_comparison.png")
print("\n   Bar heights and annotations:")
for _, row in polymer_stats.iterrows():
    print(f"   {row['polymer_name']:<16} mean={row['mean']:.1f}%  "
          f"±{row['std']:.1f}  CV={row['cv_pct']}%  n={int(row['count'])}")

print("\n" + "─" * 62)
print("  ✅ Task 2 complete. Confirm chart opened, then Task 3.")
print("─" * 62)

# =============================================================
# CHART 3 — Concentration Effect Scatter Plot (2×2 Grid)
# Question: How does concentration control release per polymer?
# =============================================================

print("\n📊 Building Chart 3: Concentration vs release scatter plots...")

df_48h = df_master[df_master['time_point_hours'] == 48].copy()

fig, axes = plt.subplots(2, 2, figsize=(11, 8))
fig.suptitle(
    "Effect of Polymer Concentration on 48h Drug Release\n"
    "Each point = one valid batch   |   Shaded region = 95% confidence interval",
    fontsize=13, y=1.01
)

axes_flat = axes.flatten()

# Per-polymer r values from Phase 3 (for annotation)
r_values = {
    'PVA':        -0.862,
    'Chitosan':   -0.868,
    'PLGA 50:50': -0.974,
    'HPMC K100':  -1.000,
}

for i, polymer in enumerate(POLYMER_ORDER):
    ax      = axes_flat[i]
    subset  = df_48h[df_48h['polymer_name'] == polymer].copy()
    colour  = POLYMER_COLOURS[polymer]
    r       = r_values[polymer]
    n       = len(subset)
    n_conc  = subset['polymer_conc_pct'].nunique()

    # Regression plot with CI (ci=None when only 2 conc levels — CI unreliable)
    sns.regplot(
        data        = subset,
        x           = 'polymer_conc_pct',
        y           = 'cumulative_release_pct',
        ax          = ax,
        color       = colour,
        scatter_kws = {'s': 90, 'zorder': 3, 'alpha': 0.85, 'edgecolors': 'white'},
        line_kws    = {'linewidth': 2.2, 'linestyle': '--'},
        ci          = 95 if n_conc >= 3 else None,
    )

    # Correlation annotation box (top right corner)
    strength = "Strong" if abs(r) >= 0.8 else "Moderate"
    caveat   = f"\n⚠ n={n} (interpret with caution)" if n <= 3 else ""
    ax.text(
        0.97, 0.97,
        f"r = {r:+.3f}\n{strength} negative{caveat}",
        transform           = ax.transAxes,
        fontsize            = 9,
        verticalalignment   = 'top',
        horizontalalignment = 'right',
        bbox=dict(
            boxstyle    = 'round,pad=0.4',
            facecolor   = 'white',
            edgecolor   = colour,
            alpha       = 0.9,
            linewidth   = 1.2,
        ),
    )

    # Annotate each point with its batch code
    for _, row in subset.iterrows():
        ax.annotate(
            row['batch_code'],
            xy          = (row['polymer_conc_pct'], row['cumulative_release_pct']),
            xytext      = (3, 4),
            textcoords  = 'offset points',
            fontsize    = 7.5,
            color       = 'gray',
        )

    # Subplot formatting
    ax.set_title(polymer, fontsize=12, fontweight='bold', color=colour, pad=8)
    ax.set_xlabel("Polymer Concentration (%)", fontsize=10)
    ax.set_ylabel("48h Release (%)", fontsize=10)

    # Dynamic y-axis: expand range 5% above/below data range for visual breathing room
    y_min = max(0,   subset['cumulative_release_pct'].min() - 8)
    y_max = min(100, subset['cumulative_release_pct'].max() + 8)
    ax.set_ylim(y_min, y_max)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=100, decimals=0))

    # Add concentration values on x-axis ticks explicitly
    ax.set_xticks(sorted(subset['polymer_conc_pct'].unique()))
    ax.set_xticklabels(
        [f"{int(c)}%" for c in sorted(subset['polymer_conc_pct'].unique())],
        fontsize=9
    )

plt.tight_layout()
plt.savefig("charts/chart_03_concentration_scatter.png", bbox_inches='tight')
plt.show()

print("✅ Chart 3 saved: charts/chart_03_concentration_scatter.png")
print("\n   Per-polymer regression summary:")
print(f"   {'Polymer':<16} {'r value':<12} {'Conc levels':<14} {'Batches'}")
print("   " + "-" * 52)
for polymer in POLYMER_ORDER:
    subset = df_48h[df_48h['polymer_name'] == polymer]
    r      = r_values[polymer]
    n_conc = subset['polymer_conc_pct'].nunique()
    n      = len(subset)
    note   = " ← most tunable" if polymer == "PLGA 50:50" else ""
    print(f"   {polymer:<16} {r:+.3f}        {n_conc:<14} {n}{note}")

print("\n" + "─" * 62)
print("  ✅ Task 3 complete. Confirm chart opened, then Task 4.")
print("─" * 62)

# =============================================================
# CHART 4 — Formulation Performance Ranking (Horizontal Bar)
# Question: Which specific formulations rank highest globally?
# =============================================================

print("\n📊 Building Chart 4: Formulation performance ranking...")

from matplotlib.patches import Patch

# Sort descending by 48h release — rank 1 = highest performer
df_ranked = df_summary.sort_values(
    'avg_release_48h', ascending=False
).reset_index(drop=True)

# ── Identify best formulation per polymer ─────────────────────────
# Tie-breaking rule: when two formulations share the same avg_release_48h,
# prefer the one with more valid batches — more evidence = stronger claim.
best_indices = set()
for polymer in POLYMER_ORDER:
    subset  = df_ranked[df_ranked['polymer_name'] == polymer]
    max_val = subset['avg_release_48h'].max()
    tied    = subset[subset['avg_release_48h'] == max_val]
    best_idx = tied['valid_batches'].idxmax()  # Prefer more batches
    best_indices.add(best_idx)

# ── Y-axis labels: rank + formulation code + polymer + concentration ─
labels = [
    f"#{i+1}  {row['formulation_code']}  —  "
    f"{row['polymer_name']}  ({row['polymer_conc_pct']:.0f}% conc)"
    for i, (_, row) in enumerate(df_ranked.iterrows())
]

# ── Draw chart ─────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(12, 9))

for i, (idx, row) in enumerate(df_ranked.iterrows()):
    colour  = POLYMER_COLOURS[row['polymer_name']]
    is_best = idx in best_indices

    # Bar — best-in-class bars have solid edge to distinguish them
    ax.barh(
        i,
        row['avg_release_48h'],
        color     = colour,
        alpha     = 1.0 if is_best else 0.72,
        edgecolor = 'black' if is_best else colour,
        linewidth = 1.8  if is_best else 0.3,
        height    = 0.65,
        zorder    = 3,
    )

    # Inside bar: mixing speed — the processing parameter that varies most
    ax.text(
        row['avg_release_48h'] * 0.42,
        i,
        f"{int(row['mixing_speed_rpm'])} rpm",
        va='center', ha='center',
        fontsize=8.5, color='white', fontweight='bold',
    )

    # End of bar: release value + star for best in polymer class
    star_text = " ★" if is_best else ""
    ax.text(
        row['avg_release_48h'] + 0.8,
        i,
        f"{row['avg_release_48h']:.1f}%{star_text}",
        va='center', ha='left',
        fontsize=9.5,
        fontweight='bold' if is_best else 'normal',
        color=colour,
    )

# Y-axis and orientation
ax.set_yticks(range(len(df_ranked)))
ax.set_yticklabels(labels, fontsize=9.5)
ax.invert_yaxis()  # Rank #1 at the top

# ── Overall mean reference line ────────────────────────────────────
overall_mean = df_ranked['avg_release_48h'].mean()
ax.axvline(
    overall_mean,
    color='gray', linestyle='--', linewidth=1.2, alpha=0.7, zorder=2
)
ax.text(
    overall_mean - 0.5, 10.5,
    f"Mean: {overall_mean:.1f}%",
    fontsize=8, color='gray', va='top', ha='right',
)

# ── Polymer colour legend ──────────────────────────────────────────
legend_elements = [
    Patch(facecolor=POLYMER_COLOURS[p], alpha=0.9, label=p)
    for p in POLYMER_ORDER
]
ax.legend(
    handles        = legend_elements,
    title          = 'Polymer type',
    loc            = 'lower right',
    fontsize       = 9,
    title_fontsize = 9,
    framealpha     = 0.92,
)

# ── Axis formatting ────────────────────────────────────────────────
ax.set_xlabel("Average 48h Cumulative Release (%)", fontsize=12, labelpad=8)
ax.set_title(
    "Formulation Performance Ranking at 48 Hours\n"
    "All 12 formulations   |   ★ = best in polymer class   |   "
    "Number inside bar = mixing speed (rpm)",
    fontsize=12, pad=12
)
ax.set_xlim(0, 112)
ax.xaxis.set_major_formatter(mtick.PercentFormatter(xmax=100, decimals=0))

plt.tight_layout()
plt.savefig("charts/chart_04_formulation_ranking.png", bbox_inches='tight')
plt.show()

print("✅ Chart 4 saved: charts/chart_04_formulation_ranking.png")
print("\n   Full ranking table:")
print(f"   {'Rank':<6} {'Code':<7} {'Polymer':<16} {'48h%':<8} "
      f"{'Batches':<10} Best in class")
print("   " + "-" * 60)
for i, (idx, row) in enumerate(df_ranked.iterrows()):
    star = "★" if idx in best_indices else ""
    print(f"   #{i+1:<5} {row['formulation_code']:<7} "
          f"{row['polymer_name']:<16} "
          f"{row['avg_release_48h']:.1f}%   "
          f"{int(row['valid_batches']):<10} {star}")

print("\n" + "─" * 62)
print("  ✅ Task 4 complete. Confirm chart opened, then Task 5.")
print("─" * 62)

# =============================================================
# CHART 5 — Correlation Heatmap
# Question: Which parameters most strongly drive 48h release?
# =============================================================

print("\n📊 Building Chart 5: Correlation heatmap...")

df_48h = df_master[df_master['time_point_hours'] == 48].copy()

# Select the analytical columns and rename for clean display labels.
# molecular_weight_kda is included deliberately — it captures polymer
# identity in a continuous way, revealing whether MW itself (not just
# polymer type) correlates with release behaviour.
corr_cols = {
    'polymer_conc_pct':       'Conc %',
    'mixing_speed_rpm':       'Mixing RPM',
    'temperature_c':          'Temp °C',
    'drug_loading_pct':       'Drug Load %',
    'molecular_weight_kda':   'MW (kDa)',
    'yield_pct':              'Yield %',
    'burst_ratio':            'Burst Ratio',
    'cumulative_release_pct': '48h Release',
}

df_corr     = df_48h[list(corr_cols.keys())].rename(columns=corr_cols)
corr_matrix = df_corr.corr()

# Mask the upper triangle (k=1 keeps diagonal visible, masks above it).
# Lower triangle + diagonal = all unique relationships, no duplication.
mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)

fig, ax = plt.subplots(figsize=(10, 8))

sns.heatmap(
    corr_matrix,
    mask       = mask,
    ax         = ax,
    annot      = True,
    fmt        = '.2f',
    cmap       = 'RdBu_r',
    vmin       = -1,
    vmax       =  1,
    center     =  0,
    square     = True,
    linewidths = 0.5,
    linecolor  = 'white',
    annot_kws  = {'size': 9},
    cbar_kws   = {'shrink': 0.75, 'label': 'Pearson r'},
)

# Highlight the '48h Release' row — the target variable.
# A black outline separates the thing we want to predict from the predictors.
n = len(corr_matrix)
ax.add_patch(plt.Rectangle(
    (0, n - 1), n, 1,
    fill=False, edgecolor='black', linewidth=2.5,
    clip_on=False, zorder=5,
))
ax.text(
    -0.12, n - 0.5,
    '← target',
    ha='right', va='center',
    fontsize=8, color='black', style='italic',
    transform=ax.transData,
)

ax.set_title(
    "Parameter Correlation Heatmap — 48h Release Endpoint\n"
    "Pearson r   |   Highlighted row = target variable   |   "
    "Lower triangle only (symmetric matrix)",
    fontsize=12, pad=12,
)
ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right', fontsize=9)
ax.set_yticklabels(ax.get_yticklabels(), rotation=0,  fontsize=9)

plt.tight_layout()
plt.savefig("charts/chart_05_correlation_heatmap.png", bbox_inches='tight')
plt.show()

print("✅ Chart 5 saved: charts/chart_05_correlation_heatmap.png")

# ── Console summary: correlations with 48h Release, sorted by strength ──
print("\n   Correlations with 48h Release — ranked by absolute strength:")
print(f"   {'Parameter':<22} {'r value':<12} Visual strength")
print("   " + "-" * 52)

target_corrs = (
    corr_matrix['48h Release']
    .drop('48h Release')
    .reindex(corr_matrix['48h Release'].drop('48h Release')
             .abs().sort_values(ascending=False).index)
)

for param, r in target_corrs.items():
    bar   = "▮" * int(abs(r) * 10)
    space = "▯" * (10 - len(bar))
    print(f"   {param:<22} r = {r:+.2f}    {bar}{space}")

# ── Notable cross-parameter relationships ────────────────────────
print("\n   Notable cross-parameter correlations (non-target):")
print(f"   {'Pair':<32} r value")
print("   " + "-" * 48)

pairs_of_interest = [
    ('Conc %',      'Burst Ratio'),
    ('MW (kDa)',    '48h Release'),
    ('Yield %',     '48h Release'),
    ('Mixing RPM',  'Conc %'),
]
for col_a, col_b in pairs_of_interest:
    if col_a in corr_matrix.columns and col_b in corr_matrix.columns:
        r = corr_matrix.loc[col_a, col_b]
        print(f"   {col_a + '  ↔  ' + col_b:<32} r = {r:+.2f}")

print("\n✅ Phase 4 EDA complete — all 5 charts saved to charts/")
print("=" * 62)
print("  Charts produced:")
print("  01 — Release profiles over time (line chart)")
print("  02 — Polymer performance comparison (bar + error bars)")
print("  03 — Concentration effect per polymer (scatter + regression)")
print("  04 — Formulation ranking (horizontal bar)")
print("  05 — Parameter correlation heatmap")
print()
print("  Next: Phase 5 — Streamlit Dashboard")
print("=" * 62)