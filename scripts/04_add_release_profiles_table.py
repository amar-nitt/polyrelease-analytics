# =============================================================
# FILE:    scripts/04_add_release_profiles_table.py
# PROJECT: PolyRelease Analytics
# PHASE:   1 — Database Schema Design
# TASK:    4 — Add the release_profiles table (time-series data)
# =============================================================

import sqlite3
import math
import random

conn   = sqlite3.connect("data/polyrelease.db")
cursor = conn.cursor()
cursor.execute("PRAGMA foreign_keys = ON")

print("=" * 62)
print("  Task 4 — Creating the release_profiles table")
print("=" * 62)
print("✅ Connected to: data/polyrelease.db")

# ── 1. Create the release_profiles table ─────────────────────────
# UNIQUE(batch_id, time_point_hours) prevents duplicate measurements.
cursor.execute("""
    CREATE TABLE IF NOT EXISTS release_profiles (
        measurement_id         INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_id               INTEGER NOT NULL,
        time_point_hours       REAL    NOT NULL CHECK(time_point_hours >= 0),
        cumulative_release_pct REAL    NOT NULL CHECK(cumulative_release_pct BETWEEN 0 AND 100),
        ph_value               REAL    NOT NULL DEFAULT 6.8,
        created_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (batch_id) REFERENCES batches(batch_id),
        UNIQUE(batch_id, time_point_hours)
    )
""")
print("✅ Table 'release_profiles' created.")

# ── 2. Define release kinetics by polymer ─────────────────────────
# Based on Korsmeyer-Peppas model: release% = max × (1 − e^(−k × t^n))
# This is a real pharmacokinetic model used in drug delivery research.
# k  = rate constant (higher = faster release)
# n  = diffusion exponent (release mechanism characteristic)
# max_release = plateau % (no polymer releases 100% under these conditions)

RELEASE_PARAMS = {
    1: {"k": 0.15, "n": 0.60, "max_release": 92},  # PLGA     — sustained, slow
    2: {"k": 0.25, "n": 0.70, "max_release": 96},  # PVA      — faster, hydrophilic
    3: {"k": 0.20, "n": 0.65, "max_release": 88},  # Chitosan — moderate
    4: {"k": 0.12, "n": 0.55, "max_release": 91},  # HPMC     — slowest, matrix type
}

TIME_POINTS = [0, 1, 2, 4, 8, 12, 24, 48]  # standard dissolution time points (hours)

def generate_release_profile(polymer_id, conc_pct, batch_seed):
    """
    Generate cumulative drug release % at each time point.
    Higher polymer concentration → slower release rate (more matrix to diffuse through).
    Random noise simulates real instrument measurement variability.
    """
    random.seed(batch_seed)
    p = RELEASE_PARAMS[polymer_id]

    # Concentration effect: each 1% increase in conc slows release by 1.2%
    k_adjusted = p["k"] * (1 - 0.012 * (conc_pct - 5))
    k_adjusted = max(k_adjusted, 0.04)          # Floor: prevent k going negative

    releases = []
    for t in TIME_POINTS:
        if t == 0:
            # Initial burst release: small amount always exits immediately
            val = round(random.uniform(0.5, 3.0), 2)
        else:
            val = p["max_release"] * (1 - math.exp(-k_adjusted * (t ** p["n"])))
            val += random.uniform(-1.5, 1.5)    # Instrument measurement noise
            val = round(max(0.0, min(100.0, val)), 2)
        releases.append(val)

    # Monotonicity correction — cumulative release physically cannot decrease
    for i in range(1, len(releases)):
        if releases[i] < releases[i - 1]:
            releases[i] = round(releases[i - 1] + random.uniform(0.1, 0.5), 2)

    return releases

# ── 3. Fetch all valid batches with their formulation details ─────
valid_batches = cursor.execute("""
    SELECT b.batch_id, b.batch_code,
           f.polymer_id, f.polymer_conc_pct
    FROM   batches b
    JOIN   formulations f ON b.formulation_id = f.formulation_id
    WHERE  b.is_valid = 1
    ORDER  BY b.batch_id
""").fetchall()

n_valid    = len(valid_batches)
n_points   = len(TIME_POINTS)
n_total    = n_valid * n_points

print(f"\n🔬 Generating release profiles for {n_valid} valid batches...")
print(f"   {n_points} time points × {n_valid} batches = {n_total} measurements total")

# ── 4. Generate and insert all measurements ───────────────────────
all_measurements = []
for batch_id, batch_code, polymer_id, conc_pct in valid_batches:
    release_values = generate_release_profile(polymer_id, conc_pct, batch_seed=batch_id * 7)
    for t, release_pct in zip(TIME_POINTS, release_values):
        all_measurements.append((batch_id, t, release_pct, 6.8))

cursor.executemany("""
    INSERT OR IGNORE INTO release_profiles
        (batch_id, time_point_hours, cumulative_release_pct, ph_value)
    VALUES (?, ?, ?, ?)
""", all_measurements)

conn.commit()
print(f"✅ Inserted {len(all_measurements)} release measurements.")

# ── 5. Sample view: one full batch time-series with visual bar ────
print("\n📋 Sample: release profile for B001 (PLGA 50:50, 5% concentration):")
print("-" * 52)
print(f"{'Time':<10} {'Cumul. Release %':<20} Visual")
print("-" * 52)
for row in cursor.execute("""
    SELECT time_point_hours, cumulative_release_pct
    FROM   release_profiles
    WHERE  batch_id = 1
    ORDER  BY time_point_hours
"""):
    t, rel = row
    bar = "▮" * int(rel / 5)
    print(f"{str(int(t))+'h':<10} {str(rel)+'%':<20} {bar}")

# ── 6. Average 48h release by polymer type (first preview insight) ─
print("\n📊 Average release at 48h by polymer (valid batches only):")
print("-" * 48)
print(f"{'Polymer':<16} {'Avg Release @48h':<18} {'Batches'}")
print("-" * 48)
for row in cursor.execute("""
    SELECT
        p.polymer_name,
        ROUND(AVG(r.cumulative_release_pct), 1) AS avg_release,
        COUNT(DISTINCT r.batch_id)              AS batch_count
    FROM   release_profiles r
    JOIN   batches      b ON r.batch_id       = b.batch_id
    JOIN   formulations f ON b.formulation_id = f.formulation_id
    JOIN   polymers     p ON f.polymer_id     = p.polymer_id
    WHERE  r.time_point_hours = 48
    AND    b.is_valid = 1
    GROUP  BY p.polymer_name
    ORDER  BY avg_release DESC
"""):
    polymer, avg_rel, count = row
    print(f"{polymer:<16} {str(avg_rel)+'%':<18} {count} batches")

# ── 7. Complete database record count ─────────────────────────────
print("\n📦 Final database summary:")
print("-" * 35)
for table in ["polymers", "formulations", "batches", "release_profiles"]:
    count = cursor.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"  {table:<25} {count:>4} rows")

conn.close()
print("\n🔒 Connection closed.")
print("✅ Task 4 complete — release_profiles table ready.")
print("=" * 62)
print("  ✅  PHASE 1 COMPLETE. All 4 tables built and populated.")
print("  📁  Your database lives at: data/polyrelease.db")
print("=" * 62)