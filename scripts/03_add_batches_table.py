# =============================================================
# FILE:    scripts/03_add_batches_table.py
# PROJECT: PolyRelease Analytics
# PHASE:   1 — Database Schema Design
# TASK:    3 — Add the batches table
# =============================================================

import sqlite3

conn   = sqlite3.connect("data/polyrelease.db")
cursor = conn.cursor()
cursor.execute("PRAGMA foreign_keys = ON")

print("=" * 58)
print("  Task 3 — Creating the batches table")
print("=" * 58)
print("✅ Connected to: data/polyrelease.db")

# ── 1. Create the batches table ───────────────────────────────────
# is_valid: 1 = successful batch, 0 = failed/rejected batch
# failure_reason: NULL for valid batches, text description for failed
# yield_pct: how much drug product was recovered (0–100%)
cursor.execute("""
    CREATE TABLE IF NOT EXISTS batches (
        batch_id        INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_code      TEXT    NOT NULL UNIQUE,
        formulation_id  INTEGER NOT NULL,
        batch_date      DATE    NOT NULL,
        is_valid        INTEGER NOT NULL DEFAULT 1 CHECK(is_valid IN (0, 1)),
        yield_pct       REAL             CHECK(yield_pct BETWEEN 0 AND 100),
        failure_reason  TEXT,
        notes           TEXT,
        created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (formulation_id) REFERENCES formulations(formulation_id)
    )
""")
print("✅ Table 'batches' created.")

# ── 2. Insert 24 batches — 2 per formulation, some intentionally invalid
# (code, form_id, date, is_valid, yield_pct, failure_reason, notes)
batch_data = [
    # — PLGA 50:50 batches (formulations F001–F004) ───────────────
    ("B001", 1,  "2023-01-15", 1, 88.5, None,                   "Standard run, good yield"),
    ("B002", 1,  "2023-01-22", 1, 91.2, None,                   "Repeat run for confirmation"),
    ("B003", 2,  "2023-02-08", 1, 85.0, None,                   "Slightly lower yield, acceptable"),
    ("B004", 2,  "2023-02-15", 0, 32.1, "Equipment malfunction", "Mixing head failed mid-process"),
    ("B005", 3,  "2023-03-05", 1, 90.3, None,                   "Elevated temp run, normal yield"),
    ("B006", 3,  "2023-03-12", 1, 87.6, None,                   "Replicate confirmed"),
    ("B007", 4,  "2023-04-02", 0, 18.4, "Contamination",        "Solvent batch was contaminated"),
    ("B008", 4,  "2023-04-18", 1, 86.9, None,                   "Repeated after contamination resolved"),
    # — PVA batches (formulations F005–F008) ──────────────────────
    ("B009", 5,  "2023-05-10", 1, 93.1, None,                   "Best yield in PVA series"),
    ("B010", 5,  "2023-05-17", 1, 89.4, None,                   "Consistent result"),
    ("B011", 6,  "2023-06-08", 1, 84.7, None,                   "Standard run"),
    ("B012", 6,  "2023-06-15", 0, 45.3, "Temperature excursion", "Incubator failed overnight"),
    ("B013", 7,  "2023-07-03", 1, 82.1, None,                   "Acceptable yield"),
    ("B014", 7,  "2023-07-10", 1, 85.5, None,                   "Consistent with B013"),
    ("B015", 8,  "2023-08-05", 0, 28.7, "Human error",          "Wrong solvent volume added"),
    ("B016", 8,  "2023-08-19", 1, 88.2, None,                   "Repeated with corrected protocol"),
    # — Chitosan batches (formulations F009–F010) ─────────────────
    ("B017", 9,  "2023-09-11", 1, 79.8, None,                   "Chitosan gelation observed — normal"),
    ("B018", 9,  "2023-09-18", 1, 81.3, None,                   "Replicate in acceptable range"),
    ("B019", 10, "2023-10-09", 1, 77.4, None,                   "High conc — lower yield expected"),
    ("B020", 10, "2023-10-16", 1, 80.2, None,                   "Consistent with B019"),
    # — HPMC K100 batches (formulations F011–F012) ────────────────
    ("B021", 11, "2023-11-06", 1, 86.3, None,                   "HPMC standard run"),
    ("B022", 11, "2023-11-13", 0, 51.2, "Calibration error",    "pH meter uncalibrated during run"),
    ("B023", 12, "2023-12-04", 1, 84.8, None,                   "Good final run of the year"),
    ("B024", 12, "2024-01-08", 1, 87.1, None,                   "New year repeat — consistent"),
]

cursor.executemany("""
    INSERT OR IGNORE INTO batches
        (batch_code, formulation_id, batch_date,
         is_valid, yield_pct, failure_reason, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?)
""", batch_data)

conn.commit()
print(f"✅ Inserted {len(batch_data)} batch records.")

# ── 3. Summary: valid vs invalid breakdown ────────────────────────
print("\n📊 Batch quality summary:")
print("-" * 35)
for row in cursor.execute("""
    SELECT
        CASE is_valid WHEN 1 THEN 'Valid' ELSE 'Invalid' END AS status,
        COUNT(*) AS count,
        ROUND(AVG(yield_pct), 1) AS avg_yield_pct
    FROM batches
    GROUP BY is_valid
    ORDER BY is_valid DESC
"""):
    status, count, avg_yield = row
    print(f"  {status:<10} {count:>2} batches   avg yield: {avg_yield}%")

# ── 4. Show the 5 invalid batches clearly ─────────────────────────
print("\n⚠️  Invalid batches (will be excluded in analysis):")
print("-" * 60)
print(f"{'Batch':<7} {'Formulation':<8} {'Yield%':<9} Failure Reason")
print("-" * 60)
for row in cursor.execute("""
    SELECT b.batch_code, b.formulation_id,
           b.yield_pct, b.failure_reason
    FROM batches b
    WHERE b.is_valid = 0
    ORDER BY b.batch_id
"""):
    code, fid, yield_pct, reason = row
    print(f"{code:<7} F{str(fid).zfill(3):<8} {str(yield_pct)+'%':<9} {reason}")

conn.close()
print("\n🔒 Connection closed.")
print("✅ Task 3 complete — batches table ready.")
print("-" * 58)
print("   Next: confirm output, then the final table — release_profiles.")
print("-" * 58)