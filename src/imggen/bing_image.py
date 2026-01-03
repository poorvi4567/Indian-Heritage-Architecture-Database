import pandas as pd
from bing_image_downloader import downloader
import os

# -----------------------------
# CONFIGURATION
# -----------------------------
CSV_FILE = "/data/intermediate/asi_monuments_clean.csv"   # path to your CSV file
COLUMN_NAME = "name"          # name of the column containing monument names
OUTPUT_DIR = "monument_images"         # folder where images will be saved
IMAGES_PER_MONUMENT = 3               # how many images to download
# -----------------------------

# Create output folder
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load CSV
df = pd.read_csv(CSV_FILE)

# Loop through monument names
for monument in df[COLUMN_NAME].dropna().unique():
    print(f"\n🔍 Downloading images for: {monument}")

    downloader.download(monument,
                        limit=IMAGES_PER_MONUMENT,
                        output_dir=OUTPUT_DIR,
                        adult_filter_off=True,
                        force_replace=False,
                        timeout=60)

print("\n✅ Done! Images downloaded successfully.")
