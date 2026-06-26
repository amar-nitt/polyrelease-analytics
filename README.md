# PolyRelease Analytics 🔬

### Drug Delivery Formulation Performance Analysis
*End-to-end data analytics project — SQL · Python · pandas · Streamlit*

[![Python](https://img.shields.io/badge/Python-3.14-blue)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.58-red)](https://streamlit.io/)
[![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey)](https://sqlite.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](https://opensource.org/licenses/MIT)

---

## 🔗 Live Demo

**[▶ Open Interactive Dashboard](https://amar-nitt-polyrelease-analytics.streamlit.app/)**
&nbsp;&nbsp;|&nbsp;&nbsp;
**[📁 GitHub Repository](https://github.com/amar-nitt/polyrelease-analytics)**

---

## 📌 Project Overview

In polymer drug delivery research, formulation parameters (polymer concentration, mixing speed, temperature) are typically recorded in spreadsheets while time-series drug release measurements are exported from instruments into separate files. Comparing formulations meant hours of manual copy-paste work in Excel — with no audit trail and no reproducibility.

This project replaces that manual workflow with a complete, automated analytics solution:

- **Structured** raw experimental data into a normalised SQLite database
- **Queried** performance insights using analytical SQL (JOINs, CTEs, window functions)
- **Cleaned and engineered** a master analytical dataset using Python and pandas
- **Visualised** findings with 5 EDA charts
- **Deployed** an interactive Streamlit dashboard accessible at a public URL

---

## 🧪 Background and Motivation

This project was built as part of a transition from scientific research (Marie Curie Fellowship — polymer nanotechnology and drug delivery systems) into data analytics. The dataset simulates real polymer research data using the **Korsmeyer–Peppas pharmacokinetic model** to generate scientifically realistic drug release profiles.

The project demonstrates that the core skills of research — hypothesis-driven thinking, working with noisy data, statistical reasoning, and evidence-based conclusions — translate directly into modern data analytics workflows.

---

## 📊 Key Findings

| Finding | Result |
|---------|--------|
| Best performing polymer at 48h | **PVA — 92.5% mean release** |
| Slowest releasing polymer at 48h | **HPMC K100 — 53.5% mean release** |
| Performance gap between extremes | **39 percentage points** |
| Strongest single predictor of 48h release | **Burst ratio (r = +0.84)** |
| Most tunable polymer by concentration | **PLGA 50:50 (Δ = −7.3% across range)** |
| Process consistency (CV) across polymers | **1.4% – 5.1% — highly reproducible** |
| Confounding variable discovered | **Mixing speed ↔ Concentration (r = +0.88)** |

---

## 🛠️ Tech Stack

| Layer | Tools Used |
|-------|-----------|
| Database | SQLite (via Python `sqlite3`) |
| Data processing | Python, pandas, NumPy |
| Static visualisation | matplotlib, seaborn |
| Interactive charts | Plotly |
| Dashboard | Streamlit |
| Version control | Git, GitHub |
| Deployment | Streamlit Community Cloud |

---

## 📁 Project Structure

```
polyrelease_analytics/
│
├── scripts/
│   ├── 01_create_database.py         # Create SQLite DB and polymers table
│   ├── 02_add_formulations_table.py  # Add formulations table
│   ├── 03_add_batches_table.py       # Add batches table with quality flags
│   ├── 04_add_release_profiles_table.py  # Add time-series measurements
│   ├── 05_analytical_queries.py      # 4 SQL analytical queries
│   ├── 06_data_pipeline.py           # Python cleaning and feature engineering
│   └── 07_eda.py                     # 5 EDA charts
│
├── dashboard/
│   └── app.py                        # Streamlit interactive dashboard
│
├── data/
│   ├── polyrelease.db                # SQLite database (4 tables, 152 rows)
│   ├── master_analytical.csv         # 152-row merged time-series dataset
│   └── formulation_summary.csv       # 12-row aggregated formulation summary
│
├── charts/
│   ├── chart_01_release_profiles.png
│   ├── chart_02_polymer_comparison.png
│   ├── chart_03_concentration_scatter.png
│   ├── chart_04_formulation_ranking.png
│   └── chart_05_correlation_heatmap.png
│
├── requirements.txt                  # 6 Python dependencies
└── .gitignore                        # Excludes venv, cache, IDE files
```

---

## 🗄️ Database Schema

```
POLYMERS ──────────► FORMULATIONS ──────────► BATCHES ──────────► RELEASE_PROFILES
(4 rows)              (12 rows)                (24 rows)            (152 rows)
reference table       experimental params      each lab run         time-series data
polymer_id PK         formulation_id PK        batch_id PK          measurement_id PK
polymer_name          polymer_id FK            formulation_id FK    batch_id FK
polymer_type          polymer_conc_pct         batch_date           time_point_hours
molecular_weight_kda  mixing_speed_rpm         is_valid             cumulative_release_pct
supplier              drug_loading_pct         yield_pct            ph_value
                      solvent                  failure_reason
```

**Design decisions:**
- Foreign keys enforce referential integrity across all 4 tables
- CHECK constraints reject physically impossible values at the database level
- Failed batches are flagged (`is_valid = 0`), never deleted — preserved for audit

---

## 📈 SQL Concepts Demonstrated

| Query | Concept |
|-------|---------|
| Polymer performance at 48h | Multi-table JOIN, GROUP BY, aggregation |
| Concentration effect on release | Conditional aggregation — `AVG(CASE WHEN ...)` |
| Formulation rankings | CTE + `RANK() OVER (PARTITION BY ...)` window function |
| Release behaviour classification | Derived metric + `CASE WHEN` segmentation |

---

## 🐍 Python / pandas Concepts Demonstrated

- `pd.read_sql_query()` — load SQL results directly into DataFrames
- `pd.merge()` — four-table chain merge (equivalent of SQL JOINs)
- `.astype()`, `pd.to_datetime()`, `pd.Categorical()` — dtype corrections
- `.fillna()`, `.dropna()` — null handling with intent distinction
- `.groupby().agg()` — multi-column aggregation
- `pd.cut()` — continuous variable binning (Low / Medium / High)
- `np.select()` — vectorised conditional classification (equivalent of CASE WHEN)
- `.pivot_table()` — reshaping time-series data for burst ratio calculation
- `.corr()` — Pearson correlation matrix
- `.describe()` — descriptive statistics with mean/median divergence check

---

## 📊 Dashboard Features

The Streamlit dashboard has three tabs, all responding to a live sidebar filter:

**Sidebar controls:**
- Polymer multiselect — filter all charts to selected polymers only
- Time-point slider — change the analysis endpoint (0h to 48h)

**Tab 1 — Release Profiles:**
Interactive Plotly line chart showing average cumulative drug release over time per polymer, with hover tooltips, legend toggling, and a summary table at four key time points.

**Tab 2 — Formulation Comparison:**
Side-by-side ranking bar chart and concentration scatter plot, both updating live with the time-point slider. Best-in-class formulations marked with ★, ties broken by batch count.

**Tab 3 — Key Findings:**
Four analytical findings in plain prose, a highlighted warning for low-sample-size results, and collapsible methodology and limitations sections.

---

## 🚀 Running Locally

**Prerequisites:** Python 3.x, Git

```bash
# Clone the repository
git clone https://github.com/amar-nitt/polyrelease-analytics.git
cd polyrelease-analytics

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows PowerShell
# source .venv/bin/activate       # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Run the dashboard
streamlit run dashboard/app.py
```

The database and CSV files are included in the repository — no need to run the setup scripts to use the dashboard. To rebuild the database from scratch, run scripts 01 through 07 in sequence from the project root.

---

## ⚠️ Known Limitations

- Dataset is synthetic, generated using the Korsmeyer–Peppas pharmacokinetic model. Results are scientifically plausible but not from real experiments.
- HPMC K100 has only 3 valid batches — findings for this polymer should be treated as directional rather than statistically conclusive.
- Mixing speed and polymer concentration are confounded (r = +0.88) in this dataset — their independent effects cannot be separated without a redesigned experiment.
- No formulation reached truly "Sustained" release behaviour (burst ratio < 13%), suggesting the tested formulation space may need expansion.

---

## 👤 About

Built by **Amar** — researcher transitioning into data analytics.

Marie Curie Research Fellowship | Polymer nanotechnology and drug delivery systems | Self-taught Python, SQL, pandas, and Streamlit.

[![GitHub](https://img.shields.io/badge/GitHub-amar--nitt-black)](https://github.com/amar-nitt)

---

*PolyRelease Analytics — Built with Python, SQL, and Streamlit*
