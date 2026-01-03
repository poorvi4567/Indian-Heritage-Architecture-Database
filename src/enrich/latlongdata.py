"""
Latitude–Longitude Generation using Geocoding API
-------------------------------------------------
This script:
1. Loads ASI enriched dataset
2. Uses city + state + India for geocoding
3. Generates latitude and longitude
4. Saves geocoded dataset

API:
- OpenStreetMap Nominatim (FREE)
"""

import pandas as pd
import os
import time
from geopy.geocoders import Nominatim
from dotenv import load_dotenv

# ==============================
# 1. Load Environment Variables
# ==============================

load_dotenv()

# ==============================
# 2. File Paths
# ==============================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Go up TWO levels: enrich → src → project root
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))

DATA_DIR = os.path.join(PROJECT_ROOT, "data", "processed")


INPUT_FILE = "asi_with_years_enriched.csv"
OUTPUT_FILE = "asi_with_years_geocoded.csv"

INPUT_PATH = os.path.join(DATA_DIR, INPUT_FILE)
OUTPUT_PATH = os.path.join(DATA_DIR, OUTPUT_FILE)

# ==============================
# 3. Load Dataset
# ==============================

df = pd.read_csv(INPUT_PATH)

# ==============================
# 4. Initialize Geocoder
# ==============================

geolocator = Nominatim(
    user_agent="monument_preservation_project"
)

# ==============================
# 5. Geocoding Function
# ==============================

def get_lat_long(city, state):
    try:
        query = f"{city}, {state}, India"
        location = geolocator.geocode(query, timeout=10)
        if location:
            return location.latitude, location.longitude
        else:
            return None, None
    except Exception:
        return None, None

# ==============================
# 6. Apply Geocoding
# ==============================

latitudes = []
longitudes = []

print("Starting geocoding...")

for index, row in df.iterrows():
    lat, lon = get_lat_long(row["City"], row["State"])
    latitudes.append(lat)
    longitudes.append(lon)

    # Respect rate limits
    time.sleep(1)

df["latitude"] = latitudes
df["longitude"] = longitudes

# ==============================
# 7. Report Missing Values
# ==============================

missing = df["latitude"].isna().sum()
print(f"Missing coordinates: {missing}")

# ==============================
# 8. Save Geocoded Dataset
# ==============================

df.to_csv(OUTPUT_PATH, index=False)

print("\nGEOCODING COMPLETED SUCCESSFULLY")
print(f"Geocoded file saved at:\n{OUTPUT_PATH}")

print("\nSample rows:")
print(df[["City", "State", "latitude", "longitude"]].head())
