import requests
import pandas as pd
import time

INPUT_CSV  = "data/processed/asi_with_styles.csv"
OUTPUT_CSV = "data/processed/asi_with_styles_dbpedia.csv"
DBPEDIA_ENDPOINT = "https://dbpedia.org/sparql"

HEADERS = {
    "Accept": "application/sparql-results+json",
    "User-Agent": "HeritageResearchBot/1.0"
}

def query_dbpedia_style(monument_name):
    # Clean the name: remove extra spaces
    clean_name = monument_name.strip()
    print(f"→ DBpedia lookup: {clean_name}")

    # Improved SPARQL: Checks the label and follows redirects if necessary
    sparql = f"""
    SELECT DISTINCT ?styleLabel WHERE {{
      {{
        ?monument rdfs:label "{clean_name}"@en .
      }} UNION {{
        ?redirect rdfs:label "{clean_name}"@en .
        ?redirect dbo:wikiPageRedirects ?monument .
      }}
      ?monument dbo:architecturalStyle ?style .
      ?style rdfs:label ?styleLabel .
      FILTER (lang(?styleLabel) = 'en')
    }}
    LIMIT 1
    """

    params = {"query": sparql, "format": "json"}

    try:
        response = requests.get(DBPEDIA_ENDPOINT, params=params, headers=HEADERS, timeout=20)
        response.raise_for_status()
        data = response.json()
        bindings = data.get("results", {}).get("bindings", [])

        if bindings:
            style = bindings[0]["styleLabel"]["value"]
            print(f"✔ DBpedia style found: {style}")
            return style
    except Exception as e:
        print(f"✖ DBpedia error for '{clean_name}': {e}")

    return None

def main():
    df = pd.read_csv(INPUT_CSV)

    # Ensure the column exists and is string type to avoid assignment issues
    if "architectural_style" not in df.columns:
        df["architectural_style"] = None
    
    # Use a copy to avoid SettingWithCopy warnings
    filled = 0

    for idx, row in df.iterrows():
        # Check if style is already present (None, NaN, or empty string)
        current_style = row.get("architectural_style")
        if pd.notna(current_style) and str(current_style).strip() != "":
            continue 

        name = row.get("asi_name") or row.get("Name")
        if not name or not isinstance(name, str):
            continue

        style = query_dbpedia_style(name)

        if style:
            df.at[idx, "architectural_style"] = style
            filled += 1
            # Save progress incrementally in case of a crash
            if filled % 10 == 0:
                df.to_csv(OUTPUT_CSV, index=False)

        time.sleep(1.0) 

    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\n✔ Enrichment complete. Filled {filled} new styles.")

if __name__ == "__main__":
    main()