# import os
# import time
# import pandas as pd
# from dotenv import load_dotenv
# import google.generativeai as genai

# # --------------------------------------------------
# # CONFIG
# # --------------------------------------------------
# INPUT_CSV  = "data/processed/asi_with_styles.csv"
# OUTPUT_CSV = "data/processed/asi_with_styles_gemini.csv"

# SLEEP_SECONDS = 70   # SAFE for Gemini free tier (5 req/min)

# # --------------------------------------------------
# # LOAD ENV
# # --------------------------------------------------
# load_dotenv()
# API_KEY = os.getenv("GEMINI_API_KEY")

# if not API_KEY:
#     raise ValueError("❌ GEMINI_API_KEY not found in .env file")

# genai.configure(api_key=API_KEY)

# # Use free-tier supported model
# MODEL_NAME = "gemini-2.5-flash"

# model = genai.GenerativeModel(MODEL_NAME)

# # --------------------------------------------------
# # PROMPT FUNCTION
# # --------------------------------------------------
# def generate_style(monument_name):
#     prompt = f"""
# Monument name: {monument_name}

# Task:
# Identify the architectural style of this monument.

# Instructions:
# - Return a short architectural style name of one word or short phrase
# - Do NOT choose from a predefined list
# - If uncertain, give the most commonly cited architectural style

# """

#     try:
#         response = model.generate_content(prompt)
#         return response.text.strip()
#     except Exception as e:
#         print(f"⚠ Gemini error for '{monument_name}': {e}")
#         return None

# # --------------------------------------------------
# # MAIN ENRICHMENT LOGIC
# # --------------------------------------------------
# def main():
#     df = pd.read_csv(INPUT_CSV)

#     if "architectural_style" not in df.columns:
#         raise ValueError("❌ 'architectural_style' column not found in CSV")

#     updated_styles = []
#     total_missing = df["architectural_style"].isna().sum()

#     print(f"\n🔎 Missing architectural styles: {total_missing}\n")

#     for idx, row in df.iterrows():
#         current_style = row.get("architectural_style")

#         # Keep existing style
#         if pd.notna(current_style) and str(current_style).strip() != "":
#             updated_styles.append(current_style)
#             continue

#         monument_name = row.get("raw_text") or row.get("Name") or "Unknown monument"
#         print(f"⏳ Gemini request for: {monument_name}")

#         style = generate_style(monument_name)
#         updated_styles.append(style)

#         print(f"✔ Result: {style}")
#         print(f"⏸ Sleeping {SLEEP_SECONDS}s to respect rate limit...\n")
#         time.sleep(SLEEP_SECONDS)

#         # Save progress every row (VERY IMPORTANT)
#         df["architectural_style"] = updated_styles + [None] * (len(df) - len(updated_styles))
#         df.to_csv(OUTPUT_CSV, index=False)

#     print("\n✅ Gemini enrichment completed")
#     print(f"📁 Output saved to: {OUTPUT_CSV}")

# # --------------------------------------------------
# if __name__ == "__main__":
#     main()

import os
import time
import pandas as pd
from dotenv import load_dotenv
import google.generativeai as genai
from google.api_core import exceptions

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
INPUT_CSV  = "data/processed/asi_with_styles_gemini.csv"
OUTPUT_CSV = "data/processed/asi_with_styles_gemini.csv"

# Gemini 1.5 Flash free tier allows ~15 Requests Per Minute (RPM)
# 12-15 seconds is usually safe, but 20s is very stable.
SLEEP_SECONDS = 70  

# --------------------------------------------------
# LOAD ENV & MODEL
# --------------------------------------------------
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("❌ GEMINI_API_KEY not found in .env file")

genai.configure(api_key=API_KEY)

# Use valid model name: gemini-1.5-flash or gemini-2.0-flash-exp
MODEL_NAME = "gemini-2.5-flash"
model = genai.GenerativeModel(MODEL_NAME)

def generate_style(monument_name):
    prompt = f"Identify the architectural style of the monument: {monument_name}. Return only a short phrase or name."
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except exceptions.ResourceExhausted:
        print("🛑 Rate limit reached (429).")
        return "RATE_LIMIT_HIT"
    except Exception as e:
        print(f"⚠ Gemini error for '{monument_name}': {e}")
        return None

def main():
    # RESUME LOGIC: Check if we already have an output file
    if os.path.exists(OUTPUT_CSV):
        print(f"📂 Found existing output file. Resuming progress...")
        df = pd.read_csv(OUTPUT_CSV)
    else:
        print(f"📄 No output file found. Starting fresh from input...")
        df = pd.read_csv(INPUT_CSV)

    if "architectural_style" not in df.columns:
        df["architectural_style"] = None

    # Identify rows that actually need filling
    mask = df["architectural_style"].isna() | (df["architectural_style"] == "")
    rows_to_process = df[mask]

    print(f"🔎 Total rows to process: {len(rows_to_process)}\n")

    for idx, row in rows_to_process.iterrows():
        monument_name = row.get("raw_text") or row.get("Name") or "Unknown monument"
        
        print(f"⏳ Requesting: {monument_name}")
        style = generate_style(monument_name)

        if style == "RATE_LIMIT_HIT":
            print("💾 Saving progress and exiting. Try running again in a few minutes.")
            break
        
        if style:
            df.at[idx, "architectural_style"] = style
            print(f"✔ Result: {style}")
            
            # Save after EVERY successful request so no data is lost
            df.to_csv(OUTPUT_CSV, index=False)
        
        # Respect the rate limit
        time.sleep(SLEEP_SECONDS)

    print(f"\n✅ Session complete. Progress saved to: {OUTPUT_CSV}")

if __name__ == "__main__":
    main()