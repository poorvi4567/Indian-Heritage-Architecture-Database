# import pandas as pd
# from wiki_style import WikiStyleFetcher   # make sure wiki_style.py is in same folder
# from tqdm import tqdm

# INPUT_CSV  = "data/processed/historical_monuments_filtered.csv"
# OUTPUT_CSV = "data/processed/asi_with_styles.csv"

# def main():
#     df = pd.read_csv(INPUT_CSV)
#     fetcher = WikiStyleFetcher()

#     styles = []

#     print("\n🔎 Fetching architectural styles from Wikipedia...\n")

#     for name in tqdm(df["Name"].fillna("").tolist()):
#         if not isinstance(name, str) or name.strip() == "":
#             styles.append(None)
#             continue

#         result = fetcher.get_style(name)
#         styles.append(result.get("style"))

#     df["architectural_style"] = styles
#     df.to_csv(OUTPUT_CSV, index=False)

#     print("\n✔ DONE! Saved enriched file to:")
#     print(OUTPUT_CSV)


# if __name__ == "__main__":
#     main()

import pandas as pd
from wiki_style import WikiYearFetcher   # Ensure your class file is named wiki_style.py
from tqdm import tqdm

# Update these paths as needed
INPUT_CSV  = "data/processed/asi_with_styles_gemini.csv"
OUTPUT_CSV = "data/processed/asi_with_years_enriched.csv"

def main():
    # Load the dataset
    try:
        df = pd.read_csv(INPUT_CSV)
    except FileNotFoundError:
        print(f"❌ Error: Could not find {INPUT_CSV}")
        return

    fetcher = WikiYearFetcher()
    years = []

    print("\n🔎 Fetching construction years from Wikipedia...\n")

    # Iterate through the monument names with a progress bar
    for name in tqdm(df["Name"].fillna("").tolist(), desc="Processing Monuments"):
        if not isinstance(name, str) or name.strip() == "":
            years.append(None)
            continue

        # Using the new method name from our updated fetcher
        result = fetcher.get_monument_year(name)
        
        # result is a dict: {"name": "...", "year": "..."}
        years.append(result.get("year"))

    # Add the new column and save
    df["year_built"] = years
    df.to_csv(OUTPUT_CSV, index=False)

    print(f"\n✔ DONE! Saved enriched file to: {OUTPUT_CSV}")
    print(df[["Name", "year_built"]].head()) # Preview the first few rows


if __name__ == "__main__":
    main()