# import requests
# from bs4 import BeautifulSoup
# import time


# class WikiStyleFetcher:

#     BASE_API = "https://en.wikipedia.org/w/api.php"
#     BASE_PAGE = "https://en.wikipedia.org/wiki/"

#     # Required headers (fixes 403 Forbidden)
#     HEADERS = {
#         "User-Agent": "IndianMonumentsResearchBot/1.0 (https://example.com/contact)",
#         "Accept-Language": "en-US,en;q=0.9"
#     }

#     # ------------------------------------------------------------
#     # STEP 1 — SEARCH FOR BEST MATCH PAGE (MediaWiki API)
#     # ------------------------------------------------------------
#     def search_title(self, query):
#         print(f"🔍 Searching for: {query}")

#         params = {
#             "action": "query",
#             "list": "search",
#             "srsearch": query,
#             "format": "json"
#         }

#         try:
#             r = requests.get(self.BASE_API, params=params, headers=self.HEADERS, timeout=10)
#             r.raise_for_status()
#         except Exception as e:
#             print("❌ Search request failed:", e)
#             return None

#         data = r.json()
#         results = data.get("query", {}).get("search", [])

#         if not results:
#             print("❌ No search results returned for:", query)
#             return None

#         title = results[0]["title"]
#         print(f"✅ Best match found: {title}")
#         return title

#     # ------------------------------------------------------------
#     # STEP 2 — DOWNLOAD HTML OF PAGE
#     # ------------------------------------------------------------
#     def get_html(self, title):
#         url = self.BASE_PAGE + title.replace(" ", "_")
#         print(f"🌐 Fetching HTML: {url}")

#         try:
#             r = requests.get(url, headers=self.HEADERS, timeout=10)
#             r.raise_for_status()
#         except Exception as e:
#             print("❌ Failed to fetch HTML:", e)
#             return None

#         return r.text

#     # ------------------------------------------------------------
#     # STEP 3 — EXTRACT ARCHITECTURAL STYLE FROM INFOBOX
#     # ------------------------------------------------------------
#     def extract_architectural_style(self, html):
#         soup = BeautifulSoup(html, "html.parser")
#         infobox = soup.find("table", class_="infobox")

#         if not infobox:
#             print("⚠ No infobox found")
#             return None

#         for row in infobox.find_all("tr"):
#             header = row.find("th")
#             value = row.find("td")

#             if not header or not value:
#                 continue

#             key = header.text.strip().lower()

#             if ("architectural" in key and "style" in key) or key == "style":
#                 style_value = value.text.strip()
#                 print(f"🏛 Architectural Style Found: {style_value}")
#                 return style_value

#         print("⚠ Infobox found, but no architectural style field.")
#         return None

#     # ------------------------------------------------------------
#     # HIGH-LEVEL FUNCTION: GET ARCHITECTURAL STYLE
#     # ------------------------------------------------------------
#     def get_style(self, name):
#         title = self.search_title(name)

#         if not title:
#             return {"name": name, "style": None, "error": "No Wikipedia page found"}

#         # Sleep to avoid rapid-fire requests (prevents block)
#         time.sleep(0.3)

#         html = self.get_html(title)
#         if not html:
#             return {"name": title, "style": None, "error": "HTML fetch failed"}

#         style = self.extract_architectural_style(html)
#         return {"name": title, "style": style}


# # ------------------------------------------------------------
# # TEST BLOCK — RUN THIS DIRECTLY TO VERIFY SCRIPT WORKS
# # ------------------------------------------------------------
# if __name__ == "__main__":
#     wiki = WikiStyleFetcher()

#     test_name = "Qutub Minar"
#     print(f"\n===== TESTING: {test_name} =====\n")

#     result = wiki.get_style(test_name)

#     print("\n📌 FINAL RESULT")
#     print("Title:", result["name"])
#     print("Architectural Style:", result["style"])
#     print("Error:", result.get("error"))

import requests
from bs4 import BeautifulSoup
import time
import re

class WikiYearFetcher:

    BASE_API = "https://en.wikipedia.org/w/api.php"
    BASE_PAGE = "https://en.wikipedia.org/wiki/"

    HEADERS = {
        "User-Agent": "IndianMonumentsResearchBot/1.0 (https://example.com/contact)",
        "Accept-Language": "en-US,en;q=0.9"
    }

    def search_title(self, query):
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json"
        }
        try:
            r = requests.get(self.BASE_API, params=params, headers=self.HEADERS, timeout=10)
            data = r.json()
            results = data.get("query", {}).get("search", [])
            return results[0]["title"] if results else None
        except Exception:
            return None

    def get_html(self, title):
        url = self.BASE_PAGE + title.replace(" ", "_")
        try:
            r = requests.get(url, headers=self.HEADERS, timeout=10)
            return r.text
        except Exception:
            return None

    def extract_year_built(self, html):
        soup = BeautifulSoup(html, "html.parser")
        infobox = soup.find("table", class_="infobox")

        if not infobox:
            return None

        # Keywords Wikipedia commonly uses for construction dates
        date_keywords = ["built", "completed", "established", "opened", "construction started","Year built"]

        for row in infobox.find_all("tr"):
            header = row.find("th")
            value = row.find("td")

            if header and value:
                key = header.text.strip().lower()
                
                if any(kw == key or kw in key for kw in date_keywords):
                    # Clean the text: remove citations like [1] and extra whitespace
                    val_text = value.get_text(separator=" ", strip=True)
                    clean_text = re.sub(r'\[.*?\]', '', val_text)
                    return clean_text

        return "Date not found in infobox"

    def get_monument_year(self, name):
        print(f"🔎 Processing: {name}")
        title = self.search_title(name)
        if not title:
            return {"name": name, "year": None, "error": "Page not found"}

        time.sleep(0.3) # Respectful delay
        html = self.get_html(title)
        if not html:
            return {"name": title, "year": None, "error": "HTML fetch failed"}

        year = self.extract_year_built(html)
        return {"name": title, "year": year}

# ------------------------------------------------------------
# TEST
# ------------------------------------------------------------
if __name__ == "__main__":
    fetcher = WikiYearFetcher()
    
    test_monuments = ["Qutub Minar", "Taj Mahal", "India Gate"]
    
    for m in test_monuments:
        data = fetcher.get_monument_year(m)
        print(f"✅ {data['name']}: {data['year']}\n")