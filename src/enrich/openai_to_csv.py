import os
import pandas as pd
from tqdm import tqdm
from dotenv import load_dotenv
from openai import OpenAI
import time

# --------------------------------------------------
# Load environment variables
# --------------------------------------------------
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

INPUT_CSV = "data/processed/asi_with_styles.csv"
OUTPUT_CSV = "data/processed/asi_with_styles_openai.csv"


def ask_openai(monument_name):
    """
    Ask OpenAI to infer architectural style.
    Free-text answer allowed.
    """

    prompt = f"""
You are a historian specializing in Indian architecture.

What is the architectural style of the monument:
"{monument_name}"?

If the style is unknown or cannot be reliably determined,
respond with: Unknown.

Respond in one short phrase only.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("❌ OpenAI error:", e)
        return None


def main():
    df = pd.read_csv(INPUT_CSV)

    if "architectural_style" not in df.columns:
        raise ValueError("architectural_style column not found")

    styles = []
    sources = []

    print("\n🤖 Enriching missing architectural styles using OpenAI...\n")

    for _, row in tqdm(df.iterrows(), total=len(df)):
        name = row.get("raw_text") or row.get("monument_name") or ""

        if pd.notna(row["architectural_style"]):
            styles.append(row["architectural_style"])
            sources.append("wikipedia")
            continue

        style = ask_openai(name)

        styles.append(style)
        sources.append("openai")

        time.sleep(0.5)  # rate limit protection

    df["architectural_style"] = styles
    df["style_source"] = sources

    df.to_csv(OUTPUT_CSV, index=False)

    print("\n✅ OpenAI enrichment complete!")
    print("📁 Saved to:", OUTPUT_CSV)


if __name__ == "__main__":
    main()
