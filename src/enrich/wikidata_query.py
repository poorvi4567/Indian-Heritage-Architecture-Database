"""Enrich CSV `Year` field using Wikidata SPARQL queries.

This script reads a processed CSV, finds rows with missing `Year`, looks up
candidate Wikidata items via the search API, queries inception dates (P571)
via SPARQL in batches, does a fuzzy match between the ASI name and candidate
labels, and fills missing `Year` values when a confident match with a
year is found.

Outputs a new CSV next to the input file with suffix `_with_wikidata_years`.
"""

import re
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
from rapidfuzz import process, fuzz
from tqdm import tqdm


# Paths
BASE = Path.cwd()
PROCESSED = BASE / "data" / "processed"
LOG_DIR = BASE / "data" / "logs"

INPUT = PROCESSED / "asi_with_years_geocoded.csv"
OUT = PROCESSED / (INPUT.stem + "_with_wikidata_years" + INPUT.suffix)
LOG = LOG_DIR / "wikidata_years_log.txt"

PROCESSED.mkdir(exist_ok=True, parents=True)
LOG_DIR.mkdir(exist_ok=True, parents=True)


def log(msg: str):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"{datetime.utcnow().isoformat()}Z {msg}\n")


# Search API
SEARCH_HEADERS = {
    "User-Agent": "HeritageDB-StudentResearchProject/1.0 (mailto:poorvi@example.com)"
}


def search_wikidata(name: str, limit: int = 5):
    url = "https://www.wikidata.org/w/api.php"
    params = {
        "action": "wbsearchentities",
        "format": "json",
        "language": "en",
        "search": name,
        "limit": limit,
    }

    try:
        r = requests.get(url, params=params, headers=SEARCH_HEADERS, timeout=30)
        r.raise_for_status()
        results = r.json().get("search", [])
        return [(res["id"], res.get("label", "")) for res in results]
    except Exception as e:
        log(f"SEARCH ERROR for '{name}': {e}")
        return []


# SPARQL
SPARQL_HEADERS = SEARCH_HEADERS


def batch_query_inception(qids):
    if not qids:
        return []

    values_str = " ".join(f"wd:{qid}" for qid in qids)

    query = f"""
    SELECT ?item ?inception WHERE {{
      VALUES ?item {{ {values_str} }}
      OPTIONAL {{ ?item wdt:P571 ?inception. }}
    }}
    """

    url = "https://query.wikidata.org/sparql"
    r = requests.get(
        url, params={"query": query, "format": "json"}, headers=SPARQL_HEADERS, timeout=90
    )
    r.raise_for_status()
    return r.json()["results"]["bindings"]


def parse_year_from_literal(lit: str):
    if not lit:
        return None
    # try to find a 4-digit year
    m = re.search(r"(-?\d{4})", lit)
    if not m:
        return None
    try:
        return int(m.group(1))
    except Exception:
        return None


def fill_missing_years():
    df = pd.read_csv(INPUT)
    log(f"START Wikidata year enrichment, rows={len(df)}")

    # Normalize Year column
    if "Year" not in df.columns:
        df["Year"] = pd.NA

    df["Year"] = df["Year"].replace("", pd.NA)

    missing_mask = df["Year"].isna()
    missing_idx = df[missing_mask].index.tolist()

    if not missing_idx:
        log("No missing Year values found; nothing to do.")
        print("No missing Year values found.")
        return

    print(f"Found {len(missing_idx)} rows with missing Year; querying Wikidata...")

    # STEP 1: search candidates for missing rows
    candidate_map = {}
    for idx in tqdm(missing_idx, desc="searching"):
        name = str(df.at[idx, "Name"]).strip()
        if not name:
            candidate_map[idx] = []
            continue
        cands = search_wikidata(name, limit=5)
        candidate_map[idx] = cands
        time.sleep(0.1)

    # STEP 2: collect unique qids and batch query inception
    all_qids = {qid for c in candidate_map.values() for qid, _ in c}
    all_qids = list(all_qids)
    qid_year = {}

    batch_size = 100
    for i in tqdm(range(0, len(all_qids), batch_size), desc="sparql batches"):
        chunk = all_qids[i : i + batch_size]
        try:
            results = batch_query_inception(chunk)
        except Exception as e:
            log(f"SPARQL batch error for chunk starting at {i}: {e}")
            results = []

        for r in results:
            qid = r["item"]["value"].split("/")[-1]
            inception_val = r.get("inception", {}).get("value")
            year = parse_year_from_literal(inception_val)
            if year is not None:
                qid_year[qid] = year

        time.sleep(0.5)

    # STEP 3: fuzzy match candidates and fill year when confident
    filled = 0
    for idx in missing_idx:
        name = str(df.at[idx, "Name"]).strip()
        cands = candidate_map.get(idx, [])
        if not cands:
            continue

        labels = [lbl for _, lbl in cands]
        match = process.extractOne(name, labels, scorer=fuzz.token_sort_ratio)
        if not match:
            continue
        match_label, score, label_idx = match
        if score < 60:
            continue

        qid = cands[label_idx][0]
        year = qid_year.get(qid)
        if year is not None:
            df.at[idx, "Year"] = year
            filled += 1
            log(f"FILLED idx={idx} name='{name}' qid={qid} year={year} score={score}")

    # STEP 4: save
    df.to_csv(OUT, index=False)
    log(f"COMPLETED Wikidata year enrichment: filled={filled} out_of={len(missing_idx)} saved={OUT}")
    print(f"Done — filled {filled}/{len(missing_idx)} missing Year values. Saved to: {OUT}")


if __name__ == "__main__":
    fill_missing_years()
