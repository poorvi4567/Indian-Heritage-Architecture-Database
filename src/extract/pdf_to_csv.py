# src/extract/pdf_to_csv.py 
import pdfplumber
import re
import pandas as pd
from pathlib import Path
from datetime import datetime

# --- Paths (follow project structure) ---
BASE = Path.cwd()  # assume you run script from project root 'heritage-database'
RAW_DIR = BASE / "data" / "raw"
INTERMEDIATE_DIR = BASE / "data" / "intermediate"
LOG_DIR = BASE / "data" / "logs"

PDF_FILENAME = "CPM_List.pdf"
INPUT_PDF = RAW_DIR / PDF_FILENAME
OUT_CSV = INTERMEDIATE_DIR / "asi_raw_entries.csv"
LOG_FILE = LOG_DIR / "extract_log.txt"

# --- Ensure directories exist ---
for d in (RAW_DIR, INTERMEDIATE_DIR, LOG_DIR):
    d.mkdir(parents=True, exist_ok=True)

run_time = datetime.utcnow().isoformat() + "Z"

# --- Check input exists ---
if not INPUT_PDF.exists():
    msg = (
        f"Input PDF not found: {INPUT_PDF}\n"
        "Please place the ASI PDF at the path above and re-run.\n"
        "Expected location: data/raw/CPM_List.pdf"
    )
    # write to log and raise
    with open(LOG_FILE, "a", encoding="utf-8") as lf:
        lf.write(f"{run_time} - ERROR - {msg}\n")
    raise FileNotFoundError(msg)

# --- Extraction ---
rows = []
with pdfplumber.open(INPUT_PDF) as pdf:
    current = None
    for pageno, page in enumerate(pdf.pages, start=1):
        text = page.extract_text() or ""
        lines = text.splitlines()
        for line in lines:
            # Detect numbered entry start: "123. <text>"
            m = re.match(r'^\s*(\d+)\.\s*(.*\S.*)$', line)
            if m:
                if current:
                    rows.append(current)
                asi_slno = int(m.group(1))
                raw = m.group(2).strip()
                current = {"asi_slno": asi_slno, "raw_text": raw, "page": pageno}
            else:
                # continuation line -> append to last raw_text
                if current and line.strip():
                    current["raw_text"] += " " + line.strip()
    if current:
        rows.append(current)

# --- Save CSV ---
df = pd.DataFrame(rows)
df.to_csv(OUT_CSV, index=False, encoding="utf-8")

# --- Log results ---
with open(LOG_FILE, "a", encoding="utf-8") as lf:
    lf.write(f"{run_time} - INFO - Extracted {len(df)} numbered entries from {INPUT_PDF}\n")
    lf.write(f"{run_time} - INFO - Wrote CSV: {OUT_CSV}\n")

# --- Print summary for user ---
print(f"Input PDF: {INPUT_PDF}")
print(f"Wrote {len(df)} rows to: {OUT_CSV}")
print(f"Run log: {LOG_FILE}")
