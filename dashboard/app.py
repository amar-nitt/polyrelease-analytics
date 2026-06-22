# =============================================================
# FILE:    dashboard/app.py
# PROJECT: PolyRelease Analytics
# PHASE:   5 — Streamlit Dashboard
# TASK:    1 — App scaffold, sidebar, and KPI cards
#
# Run from project root with:
#     streamlit run dashboard/app.py
# =============================================================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ── Resolve paths relative to this script's location, not the
#    terminal's working directory. This makes the app runnable
#    from anywhere and is required for cloud deployment later.
APP_DIR  = Path(__file__).resolve().parent      # .../dashboard
DATA_DIR = APP_DIR.parent / "data"               # .../polyrelease_analytics/data

# ── Page configuration — must be the first Streamlit call ─────────
st.set_page_config(
    page_title = "PolyRelease Analytics",
    page_icon  = "🔬",
    layout     = "wide",
    initial_sidebar_state = "expanded",
)

# ── Consistent colour and ordering across all charts ─────────────
POLYMER_COLOURS = {
    'PVA':        '#2196F3',
    'Chitosan':   '#4CAF50',
    'PLGA 50:50': '#FF9800',
    'HPMC K100':  '#9C27B0',
}
POLYMER_ORDER = ['PVA', 'Chitosan', 'PLGA 50:50', 'HPMC K100']

# ── Data loading with caching ─────────────────────────────────────
# @st.cache_data caches the returned DataFrames after the first load.
# Subsequent interactions re-use the cached result instead of
# re-reading from disk — essential for responsive filtering.
@st.cache_data
def load_data():
    df_master  = pd.read_csv(DATA_DIR / "master_analytical.csv")
    df_summary = pd.read_csv(DATA_DIR / "formulation_summary.csv")
    return df_master, df_summary

df_master, df_summary = load_data()

# ── Sidebar ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔬 PolyRelease Analytics")
    st.caption("Drug Delivery Formulation Performance Analysis")
    st.markdown("---")

    st.markdown("### Filters")
    selected_polymers = st.multiselect(
        label   = "Select polymers to display",
        options = POLYMER_ORDER,
        default = POLYMER_ORDER,
        help    = "Filter all charts and metrics to selected polymers only.",
    )

    selected_time = st.select_slider(
        label   = "Analysis time point (hours)",
        options = [0, 1, 2, 4, 8, 12, 24, 48],
        value   = 48,
        help    = "Changes the time point used in comparison charts.",
    )

    st.markdown("---")
    st.markdown("### About this project")
    st.info(
        "Built on polymer drug delivery research data. "
        "Demonstrates end-to-end analytics: SQL schema design → "
        "Python data pipeline → EDA → interactive dashboard."
    )

    st.markdown("**Stack:** Python · pandas · SQLite · Plotly · Streamlit")
    st.markdown("**Data:** 4 polymers · 12 formulations · 19 valid batches · "
                "152 measurements")
    st.caption("PolyRelease Analytics — Amar | 2024")

# ── Guard: require at least one polymer selected ──────────────────
if not selected_polymers:
    st.warning("Please select at least one polymer from the sidebar to continue.")
    st.stop()

# ── Filtered DataFrames ────────────────────────────────────────────
df_filtered  = df_master[df_master['polymer_name'].isin(selected_polymers)]
df_sum_filt  = df_summary[df_summary['polymer_name'].isin(selected_polymers)]
df_timepoint = df_filtered[df_filtered['time_point_hours'] == selected_time]

# ── Main header ────────────────────────────────────────────────────
st.markdown("# PolyRelease Analytics Dashboard")
st.markdown(
    "**Drug Delivery Formulation Performance Analysis** — "
    "Polymer comparison study · January 2023 – January 2024"
)
st.markdown("---")

# ── KPI metric cards ──────────────────────────────────────────────
# Four cards across the top: standard dashboard opening pattern.
# st.metric(label, value, delta) — delta shows change vs reference.

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

# Compute KPI values from the filtered data
total_formulations = df_sum_filt['formulation_code'].nunique()
total_batches      = df_filtered['batch_id'].nunique()

avg_by_polymer     = (
    df_timepoint
    .groupby('polymer_name')['cumulative_release_pct']
    .mean()
)
best_polymer       = avg_by_polymer.idxmax()  if not avg_by_polymer.empty else "N/A"
best_release       = avg_by_polymer.max()     if not avg_by_polymer.empty else 0
overall_mean       = df_timepoint['cumulative_release_pct'].mean()
delta_vs_mean      = round(best_release - overall_mean, 1)

with kpi1:
    st.metric(
        label = "Formulations analysed",
        value = total_formulations,
        help  = "Number of unique polymer formulations in the selected filter.",
    )

with kpi2:
    st.metric(
        label = "Valid batches",
        value = total_batches,
        help  = "Batches with is_valid = True. Failed runs excluded from analysis.",
    )

with kpi3:
    st.metric(
        label = f"Best polymer at {selected_time}h",
        value = best_polymer,
        help  = f"Polymer with highest mean release at the {selected_time}h time point.",
    )

with kpi4:
    st.metric(
        label = f"Peak release at {selected_time}h",
        value = f"{best_release:.1f}%",
        delta = f"+{delta_vs_mean:.1f}% vs overall mean",
        help  = "Highest mean release across all selected formulations.",
    )

st.markdown("---")

# ── Tabs placeholder — filled in Tasks 2, 3, 4 ───────────────────
tab1, tab2, tab3 = st.tabs([
    "📈  Release Profiles",
    "🏆  Formulation Comparison",
    "💡  Key Findings",
])

with tab1:
    st.markdown("### Drug release over time")
    st.caption(
        "Hover over any point for exact values. Click polymer names in the "
        "legend to show/hide individual lines. Drag to zoom into a time window."
    )

    # ── Build the interactive line chart ───────────────────────────
    # Average release per polymer per time point, computed live from
    # the filtered DataFrame — recalculates instantly when the sidebar
    # polymer selection changes.
    avg_profiles = (
        df_filtered
        .groupby(['polymer_name', 'time_point_hours'])['cumulative_release_pct']
        .mean()
        .reset_index()
    )

    fig_line = go.Figure()

    for polymer in POLYMER_ORDER:
        if polymer not in selected_polymers:
            continue
        data = avg_profiles[avg_profiles['polymer_name'] == polymer]

        fig_line.add_trace(go.Scatter(
            x = data['time_point_hours'],
            y = data['cumulative_release_pct'],
            mode = 'lines+markers',
            name = polymer,
            line = dict(color=POLYMER_COLOURS[polymer], width=3),
            marker = dict(size=8),
            hovertemplate =
                f"<b>{polymer}</b><br>"
                "Time: %{x}h<br>"
                "Release: %{y:.1f}%<extra></extra>",
        ))

    # Shade the early burst window (0-8h) for visual reference
    fig_line.add_vrect(
        x0=0, x1=8,
        fillcolor="gray", opacity=0.08,
        line_width=0,
        annotation_text="Early burst window",
        annotation_position="top left",
        annotation_font_size=10,
        annotation_font_color="gray",
    )

    fig_line.update_layout(
        xaxis_title = "Time (hours)",
        yaxis_title = "Cumulative drug release (%)",
        yaxis_range = [0, 105],
        xaxis = dict(
            tickmode = 'array',
            tickvals = [0, 1, 2, 4, 8, 12, 24, 48],
            ticktext = ['0h','1h','2h','4h','8h','12h','24h','48h'],
        ),
        legend_title = "Polymer",
        hovermode    = "x unified",
        height       = 480,
        margin       = dict(t=20, b=20),
        plot_bgcolor = "white",
    )
    fig_line.update_yaxes(ticksuffix="%", gridcolor="#eee")
    fig_line.update_xaxes(gridcolor="#eee")

    st.plotly_chart(fig_line, use_container_width=True)

    # ── Summary table below the chart ──────────────────────────────
    st.markdown("##### Release values at selected time points")

    summary_table = (
        avg_profiles[avg_profiles['time_point_hours'].isin([1, 8, 24, 48])]
        .pivot(index='polymer_name', columns='time_point_hours',
               values='cumulative_release_pct')
        .reindex(selected_polymers)
        .round(1)
    )
    summary_table.columns = [f"{int(c)}h release (%)" for c in summary_table.columns]
    summary_table.index.name = "Polymer"

    st.dataframe(summary_table, use_container_width=True)

with tab2:
    st.markdown("### Formulation ranking and concentration effect")
    st.caption(
        f"Showing results at the **{selected_time}h** time point — "
        "change the slider in the sidebar to compare rankings at a "
        "different stage of release."
    )

    # ── Build formulation-level stats at the selected time point ────
    # Recomputed live from df_timepoint (already filtered by sidebar
    # polymer selection and time slider) — never hardcoded to 48h.
    formulation_stats = (
        df_timepoint
        .groupby(['formulation_code', 'polymer_name',
                   'polymer_conc_pct', 'mixing_speed_rpm'])
        .agg(
            avg_release   = ('cumulative_release_pct', lambda x: round(x.mean(), 1)),
            valid_batches = ('batch_id', 'nunique'),
        )
        .reset_index()
        .sort_values('avg_release', ascending=False)
        .reset_index(drop=True)
    )

    # Identify best-in-class per polymer (tie-break: more valid batches)
    best_codes = set()
    for polymer in selected_polymers:
        subset  = formulation_stats[formulation_stats['polymer_name'] == polymer]
        if subset.empty:
            continue
        max_val  = subset['avg_release'].max()
        tied     = subset[subset['avg_release'] == max_val]
        best_row = tied.loc[tied['valid_batches'].idxmax()]
        best_codes.add(best_row['formulation_code'])

    # ── Chart A: Horizontal ranking bar ──────────────────────────────
    left, right = st.columns([1, 1])

    with left:
        st.markdown("##### Formulation ranking")

        fig_rank = go.Figure()

        formulation_stats['is_best'] = formulation_stats['formulation_code'].isin(best_codes)
        formulation_stats['label'] = formulation_stats.apply(
            lambda r: f"{r['formulation_code']} ★" if r['is_best'] else r['formulation_code'],
            axis=1
        )

        fig_rank.add_trace(go.Bar(
            x = formulation_stats['avg_release'],
            y = formulation_stats['label'],
            orientation = 'h',
            marker = dict(
                color = [POLYMER_COLOURS[p] for p in formulation_stats['polymer_name']],
                line  = dict(
                    color = ['black' if b else 'rgba(0,0,0,0)' for b in formulation_stats['is_best']],
                    width = [2 if b else 0 for b in formulation_stats['is_best']],
                ),
            ),
            customdata = formulation_stats[['polymer_name', 'polymer_conc_pct',
                                             'mixing_speed_rpm', 'valid_batches']],
            hovertemplate =
                "<b>%{y}</b><br>"
                "Polymer: %{customdata[0]}<br>"
                "Concentration: %{customdata[1]}%<br>"
                "Mixing speed: %{customdata[2]} rpm<br>"
                "Release: %{x:.1f}%<br>"
                "Valid batches: %{customdata[3]}<extra></extra>",
        ))

        fig_rank.update_layout(
            xaxis_title = f"{selected_time}h cumulative release (%)",
            yaxis = dict(autorange="reversed"),
            height = 420,
            margin = dict(t=10, b=10, l=10),
            plot_bgcolor = "white",
        )
        fig_rank.update_xaxes(ticksuffix="%", gridcolor="#eee", range=[0, 105])

        st.plotly_chart(fig_rank, use_container_width=True)
        st.caption("★ = best performer within its polymer group, by batch count when tied.")

    # ── Chart B: Concentration vs release scatter ────────────────────
    with right:
        st.markdown("##### Concentration effect")

        fig_scatter = go.Figure()

        for polymer in POLYMER_ORDER:
            if polymer not in selected_polymers:
                continue
            subset = df_timepoint[df_timepoint['polymer_name'] == polymer]
            if subset.empty:
                continue

            fig_scatter.add_trace(go.Scatter(
                x = subset['polymer_conc_pct'],
                y = subset['cumulative_release_pct'],
                mode = 'markers',
                name = polymer,
                marker = dict(color=POLYMER_COLOURS[polymer], size=11,
                               line=dict(color='white', width=1)),
                text = subset['batch_code'],
                hovertemplate =
                    f"<b>{polymer}</b><br>"
                    "Batch: %{text}<br>"
                    "Concentration: %{x}%<br>"
                    "Release: %{y:.1f}%<extra></extra>",
            ))

            # Manual regression line — only if 2+ distinct concentration levels
            if subset['polymer_conc_pct'].nunique() >= 2:
                x_vals = subset['polymer_conc_pct'].values
                y_vals = subset['cumulative_release_pct'].values
                slope, intercept = np.polyfit(x_vals, y_vals, 1)
                x_line = np.array([x_vals.min(), x_vals.max()])
                y_line = slope * x_line + intercept

                fig_scatter.add_trace(go.Scatter(
                    x = x_line, y = y_line,
                    mode = 'lines',
                    line = dict(color=POLYMER_COLOURS[polymer], dash='dash', width=2),
                    showlegend = False,
                    hoverinfo = 'skip',
                ))

        fig_scatter.update_layout(
            xaxis_title = "Polymer concentration (%)",
            yaxis_title = f"{selected_time}h release (%)",
            height = 420,
            margin = dict(t=10, b=10, l=10),
            legend_title = "Polymer",
            plot_bgcolor = "white",
        )
        fig_scatter.update_yaxes(ticksuffix="%", gridcolor="#eee")
        fig_scatter.update_xaxes(gridcolor="#eee")

        st.plotly_chart(fig_scatter, use_container_width=True)
        st.caption("Dashed lines show the trend per polymer. Click a polymer in the legend to isolate it.")

    # ── Full ranking table ───────────────────────────────────────────
    st.markdown("##### Full ranking table")
    display_table = formulation_stats[
        ['formulation_code', 'polymer_name', 'polymer_conc_pct',
         'mixing_speed_rpm', 'avg_release', 'valid_batches', 'is_best']
    ].copy()
    display_table.columns = ['Formulation', 'Polymer', 'Conc (%)',
                              'Mixing (rpm)', f'{selected_time}h release (%)',
                              'Valid batches', 'Best in class']
    display_table['Best in class'] = display_table['Best in class'].map({True: '★', False: ''})
    st.dataframe(display_table, use_container_width=True, hide_index=True)

with tab3:
    st.markdown("### Key findings")

    # ── Headline metric strip ──────────────────────────────────────
    f1, f2, f3 = st.columns(3)
    with f1:
        st.metric("Performance gap (PVA vs HPMC)", "39.0%",
                   help="Difference in mean 48h release between fastest and slowest polymer.")
    with f2:
        st.metric("Strongest single predictor", "Burst ratio",
                   help="Pearson r = +0.84 with 48h release — expected, since burst ratio is derived from it.")
    with f3:
        st.metric("Most tunable polymer", "PLGA 50:50",
                   help="Largest within-polymer concentration effect (Δ48h = -7.3% across tested range).")

    st.markdown("---")

    # ── Finding 1 ─────────────────────────────────────────────────
    st.markdown("#### 1 · Polymer choice is the dominant performance driver")
    st.markdown(
        "PVA reaches **92.5%** mean release at 48h, while HPMC K100 reaches only "
        "**53.5%** — a **39-point gap** between the fastest- and slowest-releasing "
        "polymers tested. Both are legitimate engineering choices, not a "
        "'good vs bad' result: PVA suits applications needing rapid drug "
        "availability, while HPMC suits applications needing sustained, "
        "controlled delivery over a longer window."
    )

    # ── Finding 2 ─────────────────────────────────────────────────
    st.markdown("#### 2 · Concentration is a usable control lever — but its strength depends on the polymer")
    st.markdown(
        "Across the full dataset, polymer concentration shows a **moderate global "
        "correlation** with 48h release (r = -0.33). But this number understates "
        "the real effect — when measured **within each polymer separately**, the "
        "correlation strengthens to **r = -0.86 to -1.00**. PLGA 50:50 shows the "
        "largest practical effect, with a 7.3-point release reduction across its "
        "tested concentration range, making it the most 'tunable' polymer for "
        "formulators who need to hit a specific release target."
    )
    st.warning(
        "⚠️ **Caveat:** HPMC's r = -1.000 is based on only 3 valid batches across "
        "2 concentration levels. This should be read as directionally correct, "
        "not statistically conclusive — a perfect correlation with so few points "
        "is expected, not exceptional."
    )

    # ── Finding 3 ─────────────────────────────────────────────────
    st.markdown("#### 3 · The experimental process is highly reproducible")
    st.markdown(
        "Coefficient of variation (CV) at 48h stayed below **5.1%** for every "
        "polymer group, with PVA as low as **1.4%**. This indicates the underlying "
        "manufacturing process is consistent and well-controlled — a result worth "
        "highlighting because **process reliability is often as commercially "
        "important as peak performance.**"
    )

    # ── Finding 4 ─────────────────────────────────────────────────
    st.markdown("#### 4 · A hidden confound was identified during analysis")
    st.markdown(
        "The correlation heatmap revealed that **mixing speed and polymer "
        "concentration are themselves correlated (r = +0.88)** in this dataset — "
        "higher-concentration formulations were consistently mixed at higher "
        "RPM. This means the individual effect of mixing speed **cannot be "
        "isolated** from this dataset alone. A properly designed follow-up study "
        "would hold mixing speed constant across all concentration levels to "
        "deconfound the two variables."
    )

    st.markdown("---")

    # ── Methodology & limitations ────────────────────────────────
    with st.expander("📋 Methodology notes"):
        st.markdown("""
- **Database:** SQLite, 4 normalised tables (polymers → formulations → batches → release_profiles), enforced with CHECK constraints and foreign keys.
- **Sample:** 12 formulations across 4 polymers, 24 total batches (19 valid, 5 excluded), 152 time-series measurements.
- **Validation rule:** Batches flagged `is_valid = 0` were preserved in the raw database for audit purposes but excluded from all statistical analysis.
- **Release kinetics model:** Korsmeyer–Peppas model (`release% = max × (1 − e^(−k·t^n))`) used to generate scientifically realistic release curves with measurement noise and monotonicity correction applied.
- **Tools:** SQLite, Python (pandas, NumPy), matplotlib/seaborn for static EDA, Plotly for the interactive dashboard, Streamlit for deployment.
        """)

    with st.expander("⚠️ Known limitations"):
        st.markdown("""
- **Sample size varies by polymer** — HPMC K100 has only 3 valid batches versus 6 for PVA and PLGA, weakening confidence in HPMC-specific findings.
- **Mixing speed and concentration are confounded** (r = +0.88) — their individual effects cannot be separated in this dataset.
- **No formulation showed truly "Sustained" release behaviour** (burst ratio < 13%) — even the slowest polymer (HPMC) classified as "Intermediate," suggesting the tested formulation space may need to be expanded.
- **Single replicate conditions exist** — several formulations (e.g. F006, F002) have only 1 valid batch, meaning their values cannot be checked for batch-to-batch consistency.
        """)

    st.caption(
        "Built by Amar · PolyRelease Analytics · "
        "SQL schema design → Python pipeline → EDA → Streamlit dashboard"
    )