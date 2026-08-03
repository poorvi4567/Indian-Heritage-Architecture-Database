# 🏛️ Indian Heritage Architecture Database

A full-stack data engineering and web application project that builds a structured, queryable database of **Indian heritage monuments** — enriched with architectural styles, construction years, and geolocation — and serves it through a Django web app with an **AI-powered natural language search** interface.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Data Pipeline](#data-pipeline)
  - [1. Source Dataset](#1-source-dataset)
  - [2. Enrichment](#2-enrichment)
  - [3. Database Storage](#3-database-storage)
- [Web Application](#web-application)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Environment Variables](#environment-variables)
  - [Running the Data Pipeline](#running-the-data-pipeline)
  - [Running the Web App](#running-the-web-app)
- [Screenshots](#screenshots)
- [License](#license)

---

## Overview

India has thousands of heritage monuments of immense historical and architectural significance. This project:

1. **Sources** monument data from the `touristplacesraw.xlsx` dataset containing monument names, types, cities, states, and visitor information.
2. **Enriches** the dataset with **architectural styles** and **construction years** using **Google Gemini 2.5 Flash** and **Wikidata SPARQL**, and adds **latitude/longitude** coordinates via **OpenStreetMap Nominatim**.
3. **Stores** structured relational data (name, location, style, period) in a **SQLite** database managed by Django, and additional fields (visitor info, ratings, fees, images) in **MongoDB Atlas**.
4. **Serves** the data through a **Django** web application featuring monument listings, filtering, an interactive map, detail pages with MongoDB data, and a **natural language → SQL search** powered by the Gemini API.

---

## Architecture

```
┌──────────────────────┐
│    Source Dataset     │
│  touristplacesraw.xlsx│
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│     Enrichment       │
│                      │
│ • Gemini 2.5 Flash   │──── Architectural style & year
│ • Wikidata SPARQL    │──── Construction year
│ • OSM Nominatim      │──── Latitude / Longitude
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐     ┌──────────────────────┐
│   SQLite (Django)    │     │   MongoDB Atlas       │
│                      │     │                       │
│ • monument           │     │ • monument_details    │
│ • location           │     │   - ratings           │
│ • architectural_style│     │   - entrance fees     │
│ • period             │     │   - visit hours       │
└──────────┬───────────┘     │   - image URLs        │
           │                 │   - significance      │
           ▼                 └───────────┬───────────┘
┌──────────────────────┐                │
│    Django Web App    │◀───────────────┘
│                      │
│ • Home Page          │
│ • Monument List      │
│ • Filter View        │
│ • Interactive Map    │
│ • Monument Detail    │  ← SQL + MongoDB combined
│ • NLP Search         │  ← Gemini: English → SQL
│ • Auth (Login/Signup)│
└──────────────────────┘
```

---

## Project Structure

```
Indian-Heritage-Architecture-Database/
│
├── data/
│   ├── raw/
│   │   └── touristplacesraw.xlsx        # Source dataset
│   ├── intermediate/                     # Mid-pipeline outputs
│   │   └── asi_monuments_clean.csv
│   ├── processed/                        # Final enriched datasets
│   │   ├── historical_monuments_filtered.csv
│   │   ├── asi_with_styles_gemini.csv    # Gemini-enriched styles
│   │   ├── asi_with_years_enriched.csv   # Year data from Wikipedia
│   │   ├── asi_with_years_geocoded.csv   # With lat/long from Nominatim
│   │   └── asi_with_years_geocoded_with_wikidata_years.csv
│   └── logs/                             # Pipeline run logs
│
├── src/
│   ├── extract/
│   │   └── touristplaceextract.py        # Filter historical monuments from XLSX
│   ├── enrich/
│   │   ├── gemini_style_enrichment.py    # Gemini 2.5 Flash → architectural style
│   │   ├── gemini_year_enrichment.py     # Gemini 2.5 Flash → construction year
│   │   ├── wikidata_query.py             # Wikidata SPARQL → year (P571)
│   │   ├── wiki_style.py                 # Wikipedia infobox year scraper
│   │   ├── add_style_to_csv.py           # Batch Wikipedia year enrichment
│   │   └── latlongdata.py                # OpenStreetMap Nominatim geocoding
│   └── sql/
│       ├── schema.sql                    # PostgreSQL schema reference
│       ├── create_tables.py              # Schema runner
│       └── load_data.py                  # CSV → PostgreSQL loader
│
├── App/                                  # Django web application
│   ├── heritage_site/                    # Django project config
│   │   ├── settings.py                   # SQLite, MongoDB Atlas, Gemini config
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── asgi.py
│   ├── monuments/                        # Django app
│   │   ├── models.py                     # Location, ArchitecturalStyle, Period, Monument
│   │   ├── views.py                      # All views including NLP search
│   │   ├── urls.py                       # Route definitions
│   │   ├── admin.py                      # Admin site registration
│   │   ├── import_monuments.py           # Legacy CSV importer
│   │   ├── management/
│   │   │   └── commands/
│   │   │       └── import_heritage.py    # Django management command (SQL + MongoDB)
│   │   ├── static/css/                   # Stylesheets
│   │   └── templates/
│   │       ├── base.html                 # Base layout template
│   │       ├── home.html                 # Landing page
│   │       ├── monuments.html            # Monument list
│   │       ├── monument_detail.html      # Detail page (SQL + MongoDB data)
│   │       ├── filter.html               # Filter by state/city/style
│   │       ├── map.html                  # Interactive Leaflet.js map
│   │       ├── nlp_search.html           # Natural language search UI
│   │       ├── login.html                # Login page
│   │       └── signup.html               # Signup page
│   ├── monuments.csv                     # Dataset used for import
│   ├── manage.py
│   ├── db.sqlite3                        # SQLite database
│   └── requirements.txt                  # App-specific dependencies
│
├── requirements.txt                      # Pipeline dependencies
└── .gitignore
```

---

## Data Pipeline

### 1. Source Dataset

The primary data source is **`touristplacesraw.xlsx`** — an Excel dataset containing Indian tourist places with fields like name, type, city, state, zone, ratings, entrance fees, visit duration, and more.

The extraction script (`touristplaceextract.py`) filters this dataset for heritage-relevant entries using keywords like *fort, temple, palace, museum, heritage, monument, cave, tomb, mahal, stupa, minar*.

### 2. Enrichment

The dataset is enriched using three sources:

| Source | What It Adds | Script |
|--------|-------------|--------|
| **Google Gemini 2.5 Flash** | Architectural style | `gemini_style_enrichment.py` |
| **Google Gemini 2.5 Flash** | Construction / establishment year | `gemini_year_enrichment.py` |
| **Wikidata SPARQL** | Inception year (property P571) with fuzzy name matching | `wikidata_query.py` |
| **OpenStreetMap Nominatim** | Latitude and longitude coordinates | `latlongdata.py` |

> **Note**: Other sources (DBpedia SPARQL, OpenAI, DeepSeek, Bing Images) were explored during development but did not yield reliable results and were discarded. Their scripts remain in the repo for reference only.

### 3. Database Storage

The final enriched dataset is imported into **two databases** simultaneously via the `import_heritage` management command:

#### SQLite (via Django ORM) — Relational Data
Four normalised tables for structured querying:

| Table | Fields |
|-------|--------|
| `location` | city, state, latitude, longitude, zone |
| `architectural_style` | name, monument_type |
| `period` | year |
| `monument` | name, monument_type, zone, year + foreign keys to above |

#### MongoDB Atlas — Extended Details
A `monument_details` collection storing fields not suited for the relational model:

| Field | Description |
|-------|-------------|
| `establishment_year` | Year of establishment |
| `time_to_visit_hours` | Recommended visit duration |
| `google_review_rating` | Google Maps rating |
| `num_google_reviews_lakhs` | Number of reviews (in lakhs) |
| `entrance_fee_inr` | Entry fee in INR |
| `airport_within_50km` | Nearby airport availability |
| `weekly_off` | Closed day of the week |
| `significance` | Historical significance |
| `dslr_allowed` | Whether DSLR cameras are permitted |
| `best_time_to_visit` | Recommended season |
| `image_url` | Monument image URL |

---

## Web Application

The Django app provides the following pages:

| Route | View | Description |
|-------|------|-------------|
| `/` | `signup` | User registration page |
| `/login/` | `login` | User login page |
| `/home/` | `home` | Landing page with project description and navigation |
| `/monuments/` | `monument_list` | List of all monuments with location, style, and period |
| `/monument/<id>/` | `monument_detail` | Detail page combining SQLite data with MongoDB extended fields (ratings, fees, images) |
| `/filter/` | `filter_monuments` | Filter monuments by **state**, **city**, or **architectural style** |
| `/map/` | `monuments_map` | Interactive **Leaflet.js** map with markers for every geocoded monument |
| `/search/nlp/` | `nlp_search` | **Natural language → SQL search** powered by Gemini API |

### NLP Search (English → SQL)

The standout feature — users type plain English queries like:

- *"Show me all temples in Karnataka"*
- *"How many monuments are in Delhi?"*
- *"List forts with Mughal architectural style"*

The Gemini 2.5 Flash model converts these into **read-only SQL SELECT statements** that run against the SQLite database. Results are displayed in a table with clickable monument links. The system enforces **strictly read-only queries** — only `SELECT` statements are permitted.

---

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Data Source** | touristplacesraw.xlsx (Excel) |
| **Enrichment** | Google Gemini 2.5 Flash, Wikidata SPARQL, OpenStreetMap Nominatim |
| **Relational DB** | SQLite (via Django ORM) |
| **Document DB** | MongoDB Atlas |
| **Web Framework** | Django 5.x |
| **Frontend** | HTML, CSS, Leaflet.js (maps) |
| **NLP → SQL** | Google Gemini API (gemini-2.5-flash) |
| **Auth** | Django built-in auth (User, Group) |
| **Key Libraries** | pandas, requests, rapidfuzz, pymongo, google-generativeai, geopy, python-dotenv |

---

## Getting Started

### Prerequisites

- Python 3.10+
- A Google Gemini API key (free tier works)
- MongoDB Atlas cluster (free tier works) — or a local MongoDB instance
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/poorvi4567/Indian-Heritage-Architecture-Database.git
cd Indian-Heritage-Architecture-Database

# Switch to the feature branch with NLP search
git checkout feature/nlp-search-ui-fixes

# Create a virtual environment
python -m venv venv
source venv/bin/activate   # macOS/Linux
# venv\Scripts\activate    # Windows

# Install pipeline dependencies
pip install -r requirements.txt

# Install app dependencies
pip install -r App/requirements.txt
```

### Environment Variables

Create a `.env` file in the **project root**:

```env
GEMINI_API_KEY=your_gemini_api_key
DJANGO_SECRET_KEY=your_django_secret_key
```

MongoDB Atlas connection details are configured in `App/heritage_site/settings.py` (update the `MONGODB_URI` with your own cluster URI if needed).

### Running the Data Pipeline

Run each stage from the **project root**:

```bash
# Step 1 — Extract historical monuments from the Excel dataset
python src/extract/touristplaceextract.py

# Step 2 — Enrich with architectural styles (Gemini)
python src/enrich/gemini_style_enrichment.py

# Step 3 — Enrich with construction years (Gemini)
python src/enrich/gemini_year_enrichment.py

# Step 4 — Enrich with construction years (Wikidata SPARQL)
python src/enrich/wikidata_query.py

# Step 5 — Add latitude/longitude (OpenStreetMap Nominatim)
python src/enrich/latlongdata.py
```

> **Tip**: The Gemini enrichment scripts include rate-limit handling with sleep timers and incremental saves. They can be safely stopped and resumed.

### Running the Web App

```bash
cd App

# Run Django migrations
python manage.py migrate

# Import monument data into SQLite + MongoDB
python manage.py import_heritage monuments.csv --mongo-uri "your_mongodb_atlas_uri" --mongo-db heritage

# Create a superuser for Django admin (optional)
python manage.py createsuperuser

# Start the development server
python manage.py runserver
```

Then visit:

| Page | URL |
|------|-----|
| **Signup** | [http://localhost:8000/](http://localhost:8000/) |
| **Home** | [http://localhost:8000/home/](http://localhost:8000/home/) |
| **Monument List** | [http://localhost:8000/monuments/](http://localhost:8000/monuments/) |
| **Interactive Map** | [http://localhost:8000/map/](http://localhost:8000/map/) |
| **Filter** | [http://localhost:8000/filter/?state=Karnataka](http://localhost:8000/filter/?state=Karnataka) |
| **NLP Search** | [http://localhost:8000/search/nlp/](http://localhost:8000/search/nlp/) |
| **Admin Panel** | [http://localhost:8000/admin/](http://localhost:8000/admin/) |

---

## License

This project is for educational and research purposes. Monument data is sourced from publicly available datasets and open-knowledge resources.
