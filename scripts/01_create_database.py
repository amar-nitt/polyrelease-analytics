# =============================================================
# FILE:    scripts/01_create_database.py
# PROJECT: PolyRelease Analytics
# PHASE:   1 — Database Schema Design
# TASK:    1 — Create the database and the polymers table
# =============================================================

import sqlite3
import os

# ── 1. Create the /data directory if it doesn't exist yet ────────
os.makedirs("data", exist_ok=True)

# ── 2. Connect to SQLite ──────────────────────────────────────────
# If the .db file does not exist, SQLite creates it automatically.
conn   = sqlite3.connect("data/polyrelease.db")
cursor = conn.cursor()

print("=" * 55)
print("  PolyRelease Analytics — Database Setup")
print("=" * 55)
print("✅ Connected to:  data/polyrelease.db")

# ── 3. Create the polymers reference table ───────────────────────
# This is a LOOKUP table. It stores the 4 polymer materials used
# in experiments. Other tables will reference it by polymer_id.
cursor.execute("""
    CREATE TABLE IF NOT EXISTS polymers (
        polymer_id            INTEGER  PRIMARY KEY AUTOINCREMENT,
        polymer_name          TEXT     NOT NULL UNIQUE,
        polymer_type          TEXT     NOT NULL,
        molecular_weight_kda  REAL,
        supplier              TEXT,
        created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
print("✅ Table 'polymers' created successfully.")

# ── 4. Insert the 4 polymer materials ────────────────────────────
# These are real polymers commonly used in drug delivery research.
# INSERT OR IGNORE means re-running this script won't add duplicates.
polymer_data = [
    ("PLGA 50:50", "Biodegradable Polyester",  24.0,  "Sigma-Aldrich"),
    ("PVA",        "Synthetic Hydrophilic",     89.0,  "Merck"),
    ("Chitosan",   "Natural Biopolymer",        150.0, "TCI Chemicals"),
    ("HPMC K100",  "Cellulose Derivative",      220.0, "Colorcon"),
]

cursor.executemany("""
    INSERT OR IGNORE INTO polymers
        (polymer_name, polymer_type, molecular_weight_kda, supplier)
    VALUES (?, ?, ?, ?)
""", polymer_data)

conn.commit()
print(f"✅ Inserted {cursor.rowcount} polymer record(s).")

# ── 5. Read back and display the table to verify ─────────────────
print("\n📋 Contents of 'polymers' table:")
print("-" * 65)
print(f"{'ID':<5} {'Name':<14} {'Type':<26} {'MW (kDa)':<10} Supplier")
print("-" * 65)
for row in cursor.execute("SELECT * FROM polymers"):
    pid, name, ptype, mw, supplier, _ = row
    print(f"{pid:<5} {name:<14} {ptype:<26} {str(mw):<10} {supplier}")

conn.close()
print("\n🔒 Connection closed.")
print("✅ Task 1 complete — database file created at data/polyrelease.db")
print("─" * 55)
print("   Next: confirm this ran correctly, then we add Table 2.")
print("─" * 55)
