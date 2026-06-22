# =============================================================
# FILE:    scripts/02_add_formulations_table.py
# PROJECT: PolyRelease Analytics
# PHASE:   1 — Database Schema Design
# TASK:    2 — Add the formulations table
# =============================================================

import sqlite3

# ── 1. Connect to the existing database ──────────────────────────
conn   = sqlite3.connect("data/polyrelease.db")
cursor = conn.cursor()

# SQLite does NOT enforce foreign keys by default. This turns it on.
cursor.execute("PRAGMA foreign_keys = ON")

print("=" * 58)
print("  Task 2 — Creating the formulations table")
print("=" * 58)
print("✅ Connected to: data/polyrelease.db")

# ── 2. Create the formulations table ─────────────────────────────
# FOREIGN KEY (polymer_id) links each row back to the polymers table.
# CHECK constraints reject physically impossible values at entry time.
cursor.execute("""
    CREATE TABLE IF NOT EXISTS formulations (
        formulation_id    INTEGER  PRIMARY KEY AUTOINCREMENT,
        formulation_code  TEXT     NOT NULL UNIQUE,
        polymer_id        INTEGER  NOT NULL,
        polymer_conc_pct  REAL     NOT NULL CHECK(polymer_conc_pct  BETWEEN 1 AND 50),
        mixing_speed_rpm  INTEGER  NOT NULL CHECK(mixing_speed_rpm  BETWEEN 100 AND 1200),
        temperature_c     REAL     NOT NULL DEFAULT 25.0,
        drug_loading_pct  REAL     NOT NULL CHECK(drug_loading_pct  BETWEEN 1 AND 40),
        solvent           TEXT     NOT NULL,
        created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (polymer_id) REFERENCES polymers(polymer_id)
    )
""")
print("✅ Table 'formulations' created.")

# ── 3. Insert 12 realistic formulations ──────────────────────────
# Format: (code, polymer_id, conc_pct, mixing_rpm, temp_c, drug_pct, solvent)
# polymer_id: 1=PLGA, 2=PVA, 3=Chitosan, 4=HPMC K100
formulation_data = [
    ("F001", 1,  5.0, 200, 25.0, 10.0, "Ethanol"),
    ("F002", 1, 10.0, 400, 25.0, 10.0, "Ethanol"),
    ("F003", 1, 15.0, 600, 37.0, 15.0, "Ethanol"),
    ("F004", 1, 20.0, 800, 25.0, 20.0, "Acetone"),
    ("F005", 2,  5.0, 300, 25.0, 10.0, "Water"),
    ("F006", 2, 10.0, 600, 37.0, 15.0, "Water"),
    ("F007", 2, 15.0, 400, 25.0, 20.0, "Water"),
    ("F008", 2, 20.0, 800, 37.0, 10.0, "Water"),
    ("F009", 3, 10.0, 400, 25.0, 10.0, "Acetic Acid"),
    ("F010", 3, 20.0, 800, 37.0, 15.0, "Acetic Acid"),
    ("F011", 4, 10.0, 300, 25.0, 10.0, "Water"),
    ("F012", 4, 20.0, 600, 37.0, 20.0, "Water"),
]

cursor.executemany("""
    INSERT OR IGNORE INTO formulations
        (formulation_code, polymer_id, polymer_conc_pct,
         mixing_speed_rpm, temperature_c, drug_loading_pct, solvent)
    VALUES (?, ?, ?, ?, ?, ?, ?)
""", formulation_data)

conn.commit()
print(f"✅ Inserted {len(formulation_data)} formulation records.")

# ── 4. Verify — join with polymers table to show meaningful output ─
# Notice: we use SQL JOIN here to display polymer_name instead of the
# raw polymer_id number. This is exactly what normalisation enables.
print("\n📋 Contents of 'formulations' table (joined with polymers):")
print("-" * 72)
print(f"{'Code':<6} {'Polymer':<14} {'Conc%':<7} {'RPM':<6} {'Temp°C':<8} {'Drug%':<7} Solvent")
print("-" * 72)

query = """
    SELECT
        f.formulation_code,
        p.polymer_name,
        f.polymer_conc_pct,
        f.mixing_speed_rpm,
        f.temperature_c,
        f.drug_loading_pct,
        f.solvent
    FROM formulations f
    JOIN polymers p ON f.polymer_id = p.polymer_id
    ORDER BY f.formulation_id
"""
for row in cursor.execute(query):
    code, name, conc, rpm, temp, drug, solvent = row
    print(f"{code:<6} {name:<14} {conc:<7} {rpm:<6} {temp:<8} {drug:<7} {solvent}")

conn.close()
print("\n🔒 Connection closed.")
print("✅ Task 2 complete — formulations table ready.")
print("-" * 58)
print("   Next: confirm output, then we build the batches table.")
print("-" * 58)