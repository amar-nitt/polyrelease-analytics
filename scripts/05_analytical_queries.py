# =============================================================
# FILE:    scripts/05_analytical_queries.py
# PROJECT: PolyRelease Analytics
# PHASE:   2 — SQL Analytical Queries
# =============================================================

import sqlite3

conn   = sqlite3.connect("data/polyrelease.db")
cursor = conn.cursor()
cursor.execute("PRAGMA foreign_keys = ON")

print("=" * 62)
print("  Phase 2 — SQL Analytical Queries")
print("=" * 62)

# ── QUERY 1: Polymer performance at 48 hours ─────────────────────
# Question: Which polymer delivers the highest average release,
#           and how consistent is it across batches?
# Joins all 4 tables. Filters to valid batches and the 48h time point only.

print("\n📊 QUERY 1: Polymer performance at 48 hours")
print("─" * 62)

query_1 = """
    SELECT
        p.polymer_name,
        p.polymer_type,
        COUNT(DISTINCT b.batch_id)                          AS valid_batches,
        ROUND(AVG(r.cumulative_release_pct), 1)             AS avg_release_pct,
        ROUND(MIN(r.cumulative_release_pct), 1)             AS min_release_pct,
        ROUND(MAX(r.cumulative_release_pct), 1)             AS max_release_pct,
        ROUND(MAX(r.cumulative_release_pct)
              - MIN(r.cumulative_release_pct), 1)           AS variability_range
    FROM   release_profiles r
    JOIN   batches      b  ON r.batch_id       = b.batch_id
    JOIN   formulations f  ON b.formulation_id = f.formulation_id
    JOIN   polymers     p  ON f.polymer_id     = p.polymer_id
    WHERE  r.time_point_hours = 48
    AND    b.is_valid = 1
    GROUP  BY p.polymer_id, p.polymer_name, p.polymer_type
    ORDER  BY avg_release_pct DESC
"""

results = cursor.execute(query_1).fetchall()

# ── Display results ────────────────────────────────────────────
print(f"\n{'Rank':<5} {'Polymer':<14} {'Batches':<9} "
      f"{'Avg%':<8} {'Min%':<8} {'Max%':<8} {'Range':<8} Consistency")
print("-" * 72)

for rank, row in enumerate(results, start=1):
    name, ptype, batches, avg, mn, mx, rng = row

    # Consistency label: tighter range = more consistent
    if rng < 10:
        consistency = "★★★ Excellent"
    elif rng < 20:
        consistency = "★★  Good"
    else:
        consistency = "★   Variable"

    print(f"{rank:<5} {name:<14} {batches:<9} "
          f"{str(avg)+'%':<8} {str(mn)+'%':<8} "
          f"{str(mx)+'%':<8} {str(rng)+'%':<8} {consistency}")

# ── Plain-English interpretation ───────────────────────────────
print("\n💡 Interpretation:")
top    = results[0]
bottom = results[-1]
print(f"   • {top[0]} achieves the highest average release ({top[3]}%)")
print(f"   • {bottom[0]} releases most slowly ({bottom[3]}%) — useful for sustained delivery")
print(f"   • Compare the Range column: lower range = more reproducible across batches")
print(f"   • This answers: 'Which polymer should we select for rapid vs sustained delivery?'")

# ── QUERY 2: Effect of concentration on drug release ─────────────
# Question: As polymer concentration increases, does release decrease?
# New concept: CONDITIONAL AGGREGATION — AVG(CASE WHEN ...) pivots
# multiple time points into columns inside a single query.
# Far more efficient than three separate queries or three subquery joins.

print("\n📊 QUERY 2: Effect of polymer concentration on drug release")
print("─" * 68)

query_2 = """
    SELECT
        p.polymer_name,
        f.polymer_conc_pct,
        COUNT(DISTINCT b.batch_id)                                                     AS valid_batches,
        ROUND(AVG(CASE WHEN r.time_point_hours = 1  THEN r.cumulative_release_pct END), 1) AS release_1h,
        ROUND(AVG(CASE WHEN r.time_point_hours = 8  THEN r.cumulative_release_pct END), 1) AS release_8h,
        ROUND(AVG(CASE WHEN r.time_point_hours = 48 THEN r.cumulative_release_pct END), 1) AS release_48h
    FROM   release_profiles r
    JOIN   batches      b ON r.batch_id       = b.batch_id
    JOIN   formulations f ON b.formulation_id = f.formulation_id
    JOIN   polymers     p ON f.polymer_id     = p.polymer_id
    WHERE  b.is_valid = 1
    GROUP  BY p.polymer_id, p.polymer_name, f.polymer_conc_pct
    ORDER  BY p.polymer_name, f.polymer_conc_pct
"""

results_2 = cursor.execute(query_2).fetchall()

print(f"\n{'Polymer':<14} {'Conc%':<8} {'Batches':<9}"
      f"{'1h%':<8} {'8h%':<9} {'48h%':<9} Trend vs prev. concentration")
print("-" * 74)

current_polymer = None
prev_48h        = None

for row in results_2:
    name, conc, batches, r1h, r8h, r48h = row

    # Print blank line between polymer groups for readability
    if name != current_polymer:
        if current_polymer is not None:
            print()
        current_polymer = name
        prev_48h        = r48h
        trend           = "— baseline"
    else:
        diff  = round(r48h - prev_48h, 1)
        trend = (f"↓ {abs(diff)}% slower" if diff < -0.5 else
                 f"↑ {diff}% faster"      if diff >  0.5 else
                 "≈ no change")
        prev_48h = r48h

    print(f"{name:<14} {str(conc)+'%':<8} {batches:<9}"
          f"{str(r1h)+'%':<8} {str(r8h)+'%':<9} {str(r48h)+'%':<9} {trend}")

# ── Overall concentration effect per polymer ──────────────────────
print("\n💡 Concentration effect summary (lowest → highest conc):")
print("-" * 58)

for polymer_name in ["PLGA 50:50", "PVA", "Chitosan", "HPMC K100"]:
    rows = [r for r in results_2 if r[0] == polymer_name]
    if len(rows) >= 2:
        lo, hi   = rows[0], rows[-1]
        delta    = round(hi[5] - lo[5], 1)
        direction = "slower ✓" if delta < 0 else "faster (unexpected)"
        print(f"  {polymer_name:<14}  {lo[1]}% conc → {hi[1]}% conc   "
              f"Δ48h release: {delta:+.1f}%  {direction}")

print()
print("  Scientific meaning: more polymer = denser matrix = slower diffusion.")
print("  Business equivalent: 'increasing ingredient X reduces output rate Y.'")
print("  This is a tuneable control parameter — concentration predicts release speed.")

# ── QUERY 3: Ranking formulations with RANK() window function ─────
# Question: Which formulations rank best globally AND within their
#           own polymer class?
# New concepts:
#   CTE (WITH clause)  — name an intermediate result, query it cleanly
#   RANK() OVER (...)  — rank rows without collapsing them like GROUP BY
#   PARTITION BY       — restart the ranking within each polymer group

print("\n📊 QUERY 3: Formulation rankings — global and within-polymer")
print("─" * 68)

query_3 = """
    WITH formulation_summary AS (
        SELECT
            p.polymer_name,
            f.formulation_code,
            f.polymer_conc_pct,
            f.mixing_speed_rpm,
            COUNT(DISTINCT b.batch_id)  AS valid_batches,
            ROUND(AVG(CASE WHEN r.time_point_hours =  1
                      THEN r.cumulative_release_pct END), 1) AS avg_1h,
            ROUND(AVG(CASE WHEN r.time_point_hours = 48
                      THEN r.cumulative_release_pct END), 1) AS avg_48h
        FROM   release_profiles r
        JOIN   batches      b ON r.batch_id       = b.batch_id
        JOIN   formulations f ON b.formulation_id = f.formulation_id
        JOIN   polymers     p ON f.polymer_id     = p.polymer_id
        WHERE  b.is_valid = 1
        GROUP  BY p.polymer_id, p.polymer_name,
                  f.formulation_id, f.formulation_code,
                  f.polymer_conc_pct, f.mixing_speed_rpm
    )
    SELECT
        formulation_code,
        polymer_name,
        polymer_conc_pct,
        mixing_speed_rpm,
        valid_batches,
        avg_1h,
        avg_48h,
        RANK() OVER (ORDER BY avg_48h DESC)                              AS global_rank,
        RANK() OVER (PARTITION BY polymer_name ORDER BY avg_48h DESC)   AS rank_in_polymer
    FROM   formulation_summary
    ORDER  BY global_rank, polymer_name
"""

results_3 = cursor.execute(query_3).fetchall()

# ── Display full ranked table ──────────────────────────────────────
print(f"\n{'#':<5} {'Code':<7} {'Polymer':<14} {'Conc%':<7} "
      f"{'RPM':<6} {'1h%':<7} {'48h%':<8} {'In-Polymer Rank'}")
print("-" * 72)

current_polymer = None
for row in results_3:
    code, polymer, conc, rpm, batches, r1h, r48h, grank, prank = row

    # Print separator line between polymer groups
    if polymer != current_polymer:
        if current_polymer is not None:
            print()
        current_polymer = polymer

    # Mark the top-ranked formulation in each polymer group
    marker = " ← best in class" if prank == 1 else ""

    print(f"{grank:<5} {code:<7} {polymer:<14} {str(conc)+'%':<7} "
          f"{str(rpm):<6} {str(r1h)+'%':<7} {str(r48h)+'%':<8}"
          f"  #{prank} in {polymer}{marker}")

# ── Top recommendation per polymer ────────────────────────────────
print("\n💡 Best formulation per polymer at 48h:")
print("-" * 55)

best_per_polymer = {}
for row in results_3:
    code, polymer, conc, rpm, batches, r1h, r48h, grank, prank = row
    if prank == 1 and polymer not in best_per_polymer:
        best_per_polymer[polymer] = (code, conc, rpm, r48h, grank)

for polymer, (code, conc, rpm, r48h, grank) in sorted(
        best_per_polymer.items(), key=lambda x: -x[1][3]):
    print(f"  {polymer:<14}  {code}  ({conc}% conc, {rpm} rpm)  "
          f"→ {r48h}%  [global rank #{grank}]")

print()
print("  Insight: the globally top-ranked formulation is not always")
print("  the right choice. A formulation ranked #1 within HPMC may")
print("  be preferred specifically when slow sustained release is needed.")
print("  Ranking within context matters more than absolute ranking.")

# ── QUERY 4: Release behaviour classification using CASE WHEN ─────
# Question: Does each formulation show rapid burst or sustained release?
# New concept: CASE WHEN — SQL's conditional logic (if/elif/else per row)
# Metric: burst_ratio = release at 1h ÷ release at 48h × 100
#   > 20%  →  Rapid Burst   (front-loaded, most release in first hour)
#   13-20% →  Intermediate  (balanced profile)
#   < 13%  →  Sustained     (gradual, even release over full 48h)

print("\n📊 QUERY 4: Release behaviour classification (Burst vs Sustained)")
print("─" * 68)

query_4 = """
    WITH formulation_release AS (
        SELECT
            p.polymer_name,
            f.formulation_code,
            f.polymer_conc_pct,
            ROUND(AVG(CASE WHEN r.time_point_hours =  1
                      THEN r.cumulative_release_pct END), 1) AS avg_1h,
            ROUND(AVG(CASE WHEN r.time_point_hours =  8
                      THEN r.cumulative_release_pct END), 1) AS avg_8h,
            ROUND(AVG(CASE WHEN r.time_point_hours = 48
                      THEN r.cumulative_release_pct END), 1) AS avg_48h
        FROM   release_profiles r
        JOIN   batches      b ON r.batch_id       = b.batch_id
        JOIN   formulations f ON b.formulation_id = f.formulation_id
        JOIN   polymers     p ON f.polymer_id     = p.polymer_id
        WHERE  b.is_valid = 1
        GROUP  BY p.polymer_id, p.polymer_name,
                  f.formulation_id, f.formulation_code,
                  f.polymer_conc_pct
    )
    SELECT
        formulation_code,
        polymer_name,
        polymer_conc_pct,
        avg_1h,
        avg_8h,
        avg_48h,
        ROUND(CAST(avg_1h AS REAL) / avg_48h * 100, 1) AS burst_ratio_pct,
        CASE
            WHEN CAST(avg_1h AS REAL) / avg_48h > 0.20 THEN 'Rapid Burst'
            WHEN CAST(avg_1h AS REAL) / avg_48h < 0.13 THEN 'Sustained'
            ELSE                                             'Intermediate'
        END AS release_type
    FROM   formulation_release
    ORDER  BY burst_ratio_pct DESC
"""

results_4 = cursor.execute(query_4).fetchall()

# ── Display classification table ──────────────────────────────────
print(f"\n{'Code':<7} {'Polymer':<14} {'Conc%':<7} "
      f"{'1h%':<7} {'8h%':<7} {'48h%':<7} {'Burst Ratio':<13} Release Type")
print("-" * 76)

type_icons = {
    "Rapid Burst":  "🔴",
    "Intermediate": "🟡",
    "Sustained":    "🟢",
}

for row in results_4:
    code, polymer, conc, r1h, r8h, r48h, burst, rtype = row
    icon = type_icons.get(rtype, "")
    print(f"{code:<7} {polymer:<14} {str(conc)+'%':<7} "
          f"{str(r1h)+'%':<7} {str(r8h)+'%':<7} {str(r48h)+'%':<7} "
          f"{str(burst)+'%':<13} {icon} {rtype}")

# ── Summary count by release type ─────────────────────────────────
print("\n📋 Classification summary:")
print("-" * 42)

for row in cursor.execute("""
    WITH formulation_release AS (
        SELECT
            f.formulation_code,
            ROUND(AVG(CASE WHEN r.time_point_hours =  1
                      THEN r.cumulative_release_pct END), 1) AS avg_1h,
            ROUND(AVG(CASE WHEN r.time_point_hours = 48
                      THEN r.cumulative_release_pct END), 1) AS avg_48h
        FROM   release_profiles r
        JOIN   batches      b ON r.batch_id       = b.batch_id
        JOIN   formulations f ON b.formulation_id = f.formulation_id
        WHERE  b.is_valid = 1
        GROUP  BY f.formulation_id, f.formulation_code
    )
    SELECT
        CASE
            WHEN CAST(avg_1h AS REAL) / avg_48h > 0.20 THEN 'Rapid Burst'
            WHEN CAST(avg_1h AS REAL) / avg_48h < 0.13 THEN 'Sustained'
            ELSE                                             'Intermediate'
        END AS release_type,
        COUNT(*) AS formulation_count
    FROM   formulation_release
    GROUP  BY release_type
    ORDER  BY formulation_count DESC
"""):
    rtype, count = row
    icon = type_icons.get(rtype, "")
    bar = "▮" * count
    print(f"  {icon} {rtype:<15} {count:>2} formulations  {bar}")

# ── Polymer-level insight ─────────────────────────────────────────
print("\n💡 Polymer behaviour tendency:")
print("-" * 52)
polymer_types = {}
for row in results_4:
    code, polymer, conc, r1h, r8h, r48h, burst, rtype = row
    polymer_types.setdefault(polymer, []).append(rtype)

for polymer, types in sorted(polymer_types.items()):
    dominant = max(set(types), key=types.count)
    icon = type_icons.get(dominant, "")
    print(f"  {polymer:<16} → tends toward {icon} {dominant}")

print()
print("  Application insight: Rapid Burst formulations suit conditions")
print("  needing immediate effect. Sustained formulations suit long-term")
print("  controlled delivery. Intermediate gives flexibility for both.")
print()
print("  Business equivalent: classify customers as high/medium/low")
print("  engagement based on session frequency — identical CASE WHEN logic.")
conn.close()
