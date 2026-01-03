import pandas as pd
import os

# Paths relative to project root
RAW_DATA_PATH = os.path.join("data", "raw", "touristplacesraw.xlsx")
OUTPUT_DIR = os.path.join("data", "processed")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "historical_monuments_filtered.csv")

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load dataset
df = pd.read_excel(RAW_DATA_PATH)

# Keywords that indicate historical monuments
historical_keywords = [
    "fort", "temple", "palace", "museum", "heritage", 
    "monument", "cave", "tomb", "mahal", "stupa", "minar"
]

# Function to detect historical types
def is_historical(text):
    if isinstance(text, str):
        return any(keyword in text.lower() for keyword in historical_keywords)
    return False

# ---- Modify column name if needed (here we assume it's 'Type') ----
if "Type" not in df.columns:
    raise KeyError("Column 'Type' not found. Check your dataset column names.")

historical_df = df[df["Type"].apply(is_historical)]

# Save filtered CSV
historical_df.to_csv(OUTPUT_FILE, index=False)

print(f"Filtered CSV created: {OUTPUT_FILE}")
print("Total historical monuments found:", len(historical_df))
