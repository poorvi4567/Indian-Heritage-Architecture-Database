import os
import time
import pandas as pd
import requests
from dotenv import load_dotenv
from tqdm import tqdm

# -------------------------------------------------
# Load API key
# -------------------------------------------------
load_dotenv()
API_KEY = os.getenv("DEEPSEEK_API_KEY")

if not API_KEY:
    raise RuntimeError("DEEPSEEK_API_KEY not found in .env")

# -------------------------------------------------
# Config
# -------------------------------------------------
INPUT_CSV  = "data/processed/asi_with_styles.csv"
OUTPUT_CSV = "data/processed/asi_with_styles_deepseek.csv"

API_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL   = "deepseek-chat"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# -------------------------------------------------
# DeepSeek call
# -------------------------------------------------
def get_style_from_deepseek(monument_name):
    prompt = (
        f"Monument: {monument_name}\n\n"
        "Question: What is the architectural style of this monument?\n"
        "Answer briefly using a descriptive phrase. "
        "If uncertain, make a best historical inference based on Indian architecture."
    )

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are a heritage architecture expert."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 60
    }

    try:
        response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        return data["choices"][0]["message"]["content"].strip()

    except Exception as e:
        print(f"❌ DeepSeek error for '{monument_name}': {e}")
        return None

# -------------------------------------------------
# Main enrichment loop
# -------------------------------------------------
def main():
    df = pd.read_csv(INPUT_CSV)

    new_styles = []

    print("\n🚀 Starting DeepSeek enrichment...\n")

    for _, row in tqdm(df.iterrows(), total=len(df)):
        existing_style = row.get("architectural_style")

        # Keep existing values
        if pd.notna(existing_style) and str(existing_style).strip() != "":
            new_styles.append(existing_style)
            continue

        name = row.get("asi_name") or row.get("Name") or row.get("raw_text")

        if not isinstance(name, str) or name.strip() == "":
            new_styles.append(None)
            continue

        style = get_style_from_deepseek(name)
        new_styles.append(style)

        # Safe rate limit (avoid bans)
        time.sleep(3)

    df["architectural_style"] = new_styles
    df.to_csv(OUTPUT_CSV, index=False)

    print("\n✅ Enrichment complete!")
    print(f"📄 Saved to: {OUTPUT_CSV}")

# -------------------------------------------------
if __name__ == "__main__":
    main()
