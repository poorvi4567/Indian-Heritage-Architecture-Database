import os
import time
import pandas as pd
from dotenv import load_dotenv
import google.generativeai as genai

# =============================
# Load environment variables
# =============================
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=API_KEY)

MODEL_NAME = "gemini-2.5-flash-lite"

# =============================
# File paths
# =============================
INPUT_CSV  = "data/processed/asi_with_styles_gemini.csv"
OUTPUT_CSV = "data/processed/asi_with_styles_gemini.csv"

# =============================
# Load dataset
# =============================
df = pd.read_csv(INPUT_CSV)

# =============================
# Gemini model
# =============================
model = genai.GenerativeModel(MODEL_NAME)

# =============================
# Function to infer year
# =============================
def infer_establishment_year(monument_name):
    prompt = f"""
You are a heritage expert.

Monument name: {monument_name}

Question:
What is the establishment year or approximate time period of this monument?

Rules:
- If exact year is unknown, give approximate century or dynasty period.
- Keep answer short.
- Do NOT say "I don't know".
- Do NOT hallucinate exact years.
"""

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"❌ Gemini error for '{monument_name}': {e}")
        return None

# =============================
# Main loop (SAFE MODE)
# =============================
processed_today = 0
DAILY_LIMIT = 18   # keep buffer under free tier limit

for idx, row in df.iterrows():

    if processed_today >= DAILY_LIMIT:
        print("\n🚫 Daily Gemini quota reached. Stop and continue tomorrow.")
        break

    if str(row["Establishment Year"]).strip().lower() != "unknown":
        continue

    monument_name = row.get("Monument Name") or row.get("Name")

    print(f"\n⏳ Inferring year for: {monument_name}")

    result = infer_establishment_year(monument_name)

    if result:
        df.at[idx, "Establishment Year"] = result
        processed_today += 1
        print(f"✔ Filled: {result}")

        # Save progress immediately
        df.to_csv(OUTPUT_CSV, index=False)
    else:
        print("⚠ No result returned")

    # VERY IMPORTANT: sleep to avoid rate limit
    print("⏸ Sleeping 70 seconds...")
    time.sleep(70)

print("\n✅ Script finished safely")
print(f"Filled today: {processed_today}")
print(f"Output saved to: {OUTPUT_CSV}")
