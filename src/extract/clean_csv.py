# src/extract/clean_csv.py
import pandas as pd
import re
from pathlib import Path
from datetime import datetime

# --- Paths ---
BASE = Path.cwd()
INTERMEDIATE_DIR = BASE / "data" / "intermediate"
LOG_DIR = BASE / "data" / "logs"

IN_FILE = INTERMEDIATE_DIR / "asi_raw_entries.csv"
OUT_FILE = INTERMEDIATE_DIR / "asi_monuments_clean.csv"
LOG_FILE = LOG_DIR / "clean_csv_log.txt"

# Ensure dirs exist
INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

run_time = datetime.utcnow().isoformat() + "Z"

# Check input file
if not IN_FILE.exists():
    msg = f"Input not found: {IN_FILE}"
    with open(LOG_FILE, "a") as f:
        f.write(f"{run_time} - ERROR - {msg}\n")
    raise FileNotFoundError(msg)

df = pd.read_csv(IN_FILE)

state = None
circle = None
entries = []
header_count = 0

for _, row in df.iterrows():
    txt = str(row['raw_text']).strip()

    # --- Detect state/circle headers ---
    if ("Circle" in txt) and re.search(r'\d{1,4}', txt):
        # Example: "Andhra Pradesh     135     Amaravati Circle"
        parts = re.split(r"\s{2,}", txt)

        # First part before number is usually state
        if len(parts) >= 1:
            state = parts[0].strip()

        # Extract circle name
        circ = re.search(r"([A-Za-z &]+Circle)", txt)
        if circ:
            circle = circ.group(1).strip()

        header_count += 1
        continue

    # --- Parse monument row ---
    parts = re.split(r"\s{2,}", txt)  # split on 2+ spaces
    name = locality = district = None

    if len(parts) >= 3:
        name = parts[0].strip()
        locality = parts[1].strip()
        district = parts[2].strip()

    elif len(parts) == 2:
        name = parts[0].strip()
        locality = parts[1].strip()

    else:
        # try comma split
        parts2 = [p.strip() for p in txt.split(",") if p.strip()]
        if len(parts2) >= 3:
            name, locality, district = parts2[0], parts2[1], parts2[2]
        elif len(parts2) == 2:
            name, locality = parts2
        else:
            name = txt  # fallback

    asi_slno = int(row['asi_slno'])
    monument_id = f"ASI-{asi_slno:05d}"

    entries.append({
        "monument_id": monument_id,
        "asi_slno": asi_slno,
        "name": name,
        "locality": locality,
        "district": district,
        "state": state,
        "circle": circle,
        "page": int(row['page']),
        "raw_text": txt
    })

# --- Save output ---
clean_df = pd.DataFrame(entries)
clean_df.to_csv(OUT_FILE, index=False, encoding="utf-8")

# --- Log ---
with open(LOG_FILE, "a") as f:
    f.write(f"{run_time} - INFO - Parsed {len(clean_df)} entries, headers found: {header_count}\n")
    f.write(f"{run_time} - INFO - Output saved: {OUT_FILE}\n")

print(f"Cleaned CSV saved: {OUT_FILE}")
print(f"Detected {header_count} state/circle headers")
print(f"Structured rows: {len(clean_df)}")
