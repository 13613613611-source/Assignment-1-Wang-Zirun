# Wikipedia Famous People Scraper
# Scrape biographical information from Wikipedia Infoboxes
# Based on data/famous_people.csv

import json
import time
import os
import csv
import re
from urllib.parse import quote
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "WikiBot/1.0 (Educational Project; crawler practice)",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
}


class WikipediaScraper:
    """Scrape biographical information from Wikipedia pages."""

    def __init__(self, wait_seconds: float = 1.0):
        self.wait_seconds = wait_seconds
        self.base_url = "https://en.wikipedia.org/w/api.php"

    def fetch(self, wiki_title: str) -> dict | None:
        """
        Fetch page data from Wikipedia API.
        Returns structured data from the Infobox.
        """
        try:
            # First, get the page content in HTML format to parse Infobox
            params = {
                "action": "parse",
                "page": wiki_title,
                "format": "json",
                "prop": "text|info|categories",
                "formatversion": "2",
                "redirects": 1,
            }
            r = requests.get(self.base_url, params=params, headers=HEADERS, timeout=15)
            r.raise_for_status()
            data = r.json()
            if "parse" not in data:
                print(f"  Warning: Could not parse page: {wiki_title}")
                return None
            return data["parse"]
        except Exception as e:
            print(f"  Error fetching {wiki_title}: {e}")
            return None

    def parse_infobox(self, html_content: str, wiki_title: str) -> dict:
        """
        Extract information from the Infobox (infobox) in the HTML.
        """
        result = {
            "name": wiki_title,
            "raw_html": html_content,
        }
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            # Find the Infobox table
            infobox = (
                soup.find("table", class_="infobox")
                or soup.find("table", class_=re.compile(r"infobox", re.I))
                or soup.find("table", {"class": "vcard"})
            )
            if not infobox:
                return result

            # Extract all rows from the infobox
            for row in infobox.find_all("tr"):
                header = row.find("th")
                data = row.find("td")
                if header and data:
                    label = header.get_text(strip=True)
                    value = self._clean_infobox_value(data)
                    # Map common labels to our fields
                    result = self._map_field(result, label, value)

            # Also try to extract key-value pairs from plain text
            result["full_text_preview"] = self._extract_key_values(soup)
        except Exception as e:
            print(f"  Error parsing infobox for {wiki_title}: {e}")
        return result

    def _clean_infobox_value(self, element) -> str:
        """Clean and extract text from an infobox cell."""
        if not element:
            return ""
        # Remove references like [1], [2]
        for ref in element.find_all("sup"):
            ref.decompose()
        # Remove small notes
        for small in element.find_all("small"):
            small.decompose()
        # Get text, handling line breaks
        text = element.get_text(separator=" | ", strip=True)
        # Clean up extra whitespace
        text = re.sub(r"\s+", " ", text)
        text = text.strip()
        return text

    def _map_field(self, result: dict, label: str, value: str) -> dict:
        """Map infobox labels to standardized field names."""
        label_lower = label.lower()

        # Birth information
        if "born" in label_lower:
            if "born" not in result:
                result["born"] = value
            # Try to parse date and place
            date_match = re.match(r"([^(]+)\(([^)]+)\)", value)
            if date_match:
                result["birth_date"] = date_match.group(1).strip()
                result["birth_place"] = date_match.group(2).strip()
            else:
                result["birth_date"] = value

        # Death information
        elif "died" in label_lower:
            if "died" not in result:
                result["died"] = value
            date_match = re.match(r"([^(]+)\(([^)]+)\)", value)
            if date_match:
                result["death_date"] = date_match.group(1).strip()
                result["death_place"] = date_match.group(2).strip()
            else:
                result["death_date"] = value

        # Citizenship
        elif any(kw in label_lower for kw in ["citizen", "nationality", "country"]):
            result["citizenship"] = value

        # Education
        elif any(kw in label_lower for kw in ["educat", "alma"]):
            result["education"] = value

        # Known for
        elif "known for" in label_lower or "known" in label_lower:
            result["known_for"] = value

        # Occupation/Profession
        elif "occupation" in label_lower or "profession" in label_lower:
            result["profession"] = value

        # Spouse
        elif "spouse" in label_lower:
            if "spouse" not in result:
                result["spouse"] = []
            spouses = [s.strip() for s in value.split(" | ") if s.strip()]
            result["spouse"].extend(spouses)

        # Children
        elif "children" in label_lower:
            result["children"] = value

        # Family
        elif "family" in label_lower:
            result["family"] = value

        # Awards
        elif "award" in label_lower or "prize" in label_lower:
            result["awards"] = value

        # Fields (for scientists)
        elif "field" in label_lower:
            result["fields"] = value

        # Institutions
        elif "institution" in label_lower or "institutions" in label_lower:
            result["institutions"] = value

        # Thesis
        elif "thesis" in label_lower:
            result["thesis"] = value

        # Doctoral advisor
        elif "doctoral advisor" in label_lower or "phd advisor" in label_lower:
            result["doctoral_advisor"] = value

        # Other advisors
        elif "academic advisor" in label_lower:
            result["academic_advisor"] = value

        # Work institutions
        elif "work" in label_lower and "institution" not in label_lower:
            result["workplaces"] = value

        # Signature image
        elif "signature" in label_lower and "image" not in label_lower:
            img = value.find("img") if hasattr(value, "find") else None
            if img:
                result["signature_url"] = img.get("src", "")

        return result

    def _extract_key_values(self, soup: BeautifulSoup) -> dict:
        """Extract key-value pairs from the page content."""
        key_values = {}
        try:
            # Look for the lead section
            lead = soup.find("div", {"id": "mw-content-text"})
            if lead:
                paragraphs = lead.find_all("p", limit=3)
                if paragraphs:
                    text = " ".join([p.get_text(strip=True) for p in paragraphs])
                    key_values["description"] = text[:500]
        except Exception:
            pass
        return key_values

    def get_page_extract(self, wiki_title: str) -> str:
        """Get plain text extract from Wikipedia."""
        try:
            params = {
                "action": "query",
                "format": "json",
                "titles": wiki_title,
                "prop": "extracts",
                "exintro": True,
                "explaintext": True,
                "formatversion": "2",
                "redirects": 1,
            }
            r = requests.get(self.base_url, params=params, headers=HEADERS, timeout=15)
            r.raise_for_status()
            data = r.json()
            pages = data.get("query", {}).get("pages", [])
            if pages and "extract" in pages[0]:
                return pages[0]["extract"]
        except Exception as e:
            print(f"  Error getting extract for {wiki_title}: {e}")
        return ""

    def scrape_person(self, wiki_title: str) -> dict:
        """Scrape complete information for one person."""
        print(f"  Scraping: {wiki_title}")

        # Fetch HTML content
        parse_data = self.fetch(wiki_title)
        if not parse_data:
            return None

        # Parse infobox
        infobox_data = self.parse_infobox(parse_data.get("text", ""), wiki_title)

        # Get plain text extract
        infobox_data["description"] = self.get_page_extract(wiki_title)

        # Add metadata
        infobox_data["wiki_title"] = wiki_title
        infobox_data["wiki_url"] = f"https://en.wikipedia.org/wiki/{quote(wiki_title.replace(' ', '_'))}"

        # Get categories - handle different API response formats
        infobox_data["categories"] = []
        for cat in parse_data.get("categories", []):
            # API may return "*" or "title" as the key
            cat_title = cat.get("*") or cat.get("title", "")
            if cat_title:
                infobox_data["categories"].append(cat_title)

        return infobox_data

    def scrape_many(self, wiki_titles: list[str], verbose: bool = True) -> list[dict]:
        """Scrape multiple Wikipedia pages."""
        results = []
        for i, title in enumerate(wiki_titles, 1):
            if verbose:
                print(f"[{i}/{len(wiki_titles)}] Processing: {title}")

            person_data = self.scrape_person(title)
            if person_data:
                results.append(person_data)
                if verbose:
                    print(f"  -> Success: {person_data.get('name', title)}")

            # Rate limiting
            if i < len(wiki_titles):
                time.sleep(self.wait_seconds)

        return results

    def scrape_from_csv(self, csv_path: str, wiki_title_col: str = "wiki_title") -> list[dict]:
        """Scrape Wikipedia pages for people listed in a CSV file."""
        wiki_titles = []
        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    title = row.get(wiki_title_col, "").strip()
                    if title and title not in wiki_titles:
                        wiki_titles.append(title)
            print(f"Loaded {len(wiki_titles)} wiki titles from CSV")
        except Exception as e:
            print(f"Error reading CSV: {e}")
            return []

        return self.scrape_many(wiki_titles)


def load_famous_people(csv_path: str) -> list[dict]:
    """Load famous people data from CSV file."""
    people = []
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                people.append({
                    "name": row.get("name", ""),
                    "chinese_name": row.get("chinese_name", ""),
                    "wiki_title": row.get("wiki_title", ""),
                    "birth_year": row.get("birth_year", ""),
                    "death_year": row.get("death_year", ""),
                    "profession": row.get("profession", ""),
                    "nationality": row.get("nationality", ""),
                })
    except Exception as e:
        print(f"Error loading CSV: {e}")
    return people


def save_to_json(path: str, data: list[dict], additional_info: dict | None = None) -> None:
    """Save scraped data to JSON file."""
    try:
        dirname = os.path.dirname(path)
        if dirname:
            os.makedirs(dirname, exist_ok=True)

        output = {
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "count": len(data),
            "source": "Wikipedia",
            "data": data,
        }
        if additional_info:
            output["metadata"] = additional_info

        with open(path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(data)} records to {path}")
    except Exception as e:
        print(f"Error saving: {e}")


def main():
    """Main function to run the scraper."""
    # Configuration
    CSV_PATH = "data/famous_people.csv"
    OUTPUT_DIR = r"C:\Users\11613\Desktop\1\2026\2月\FF-260205\DATA2"

    print("=" * 60)
    print("Wikipedia Famous People Scraper")
    print("=" * 60)

    # Load source data
    print(f"\nLoading data from: {CSV_PATH}")
    people = load_famous_people(CSV_PATH)
    print(f"Loaded {len(people)} famous people")

    # Initialize scraper (with 1 second delay to be respectful)
    scraper = WikipediaScraper(wait_seconds=1.0)

    # Get wiki titles
    wiki_titles = [p["wiki_title"] for p in people if p["wiki_title"]]
    print(f"Will scrape {len(wiki_titles)} Wikipedia pages")

    # Scrape all pages
    print("\nStarting scrape...")
    print("-" * 60)

    results = scraper.scrape_many(wiki_titles, verbose=True)

    print("-" * 60)
    print(f"\nScraped {len(results)} people successfully")

    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Save full results
    output_path = os.path.join(OUTPUT_DIR, "famous_people_wikipedia.json")
    save_to_json(output_path, results, {
        "source_csv": CSV_PATH,
        "description": "Scraped Wikipedia Infobox data for 100 famous people",
        "fields_extracted": [
            "name", "born", "birth_date", "birth_place",
            "died", "death_date", "death_place",
            "citizenship", "education", "profession",
            "known_for", "spouse", "children", "family",
            "awards", "fields", "institutions", "thesis",
            "doctoral_advisor", "academic_advisor",
            "description", "wiki_url", "categories"
        ]
    })

    # Save a simplified version with key fields only
    simplified_data = []
    for person in results:
        simplified = {
            "name": person.get("name", ""),
            "wiki_title": person.get("wiki_title", ""),
            "wiki_url": person.get("wiki_url", ""),
            "birth_date": person.get("birth_date", ""),
            "birth_place": person.get("birth_place", ""),
            "death_date": person.get("death_date", ""),
            "death_place": person.get("death_place", ""),
            "profession": person.get("profession", ""),
            "citizenship": person.get("citizenship", ""),
            "known_for": person.get("known_for", ""),
            "awards": person.get("awards", "")[:200] if person.get("awards") else "",  # Limit length
            "description": person.get("description", "")[:300] if person.get("description") else "",
        }
        simplified_data.append(simplified)

    simplified_path = os.path.join(OUTPUT_DIR, "famous_people_simplified.json")
    save_to_json(simplified_path, simplified_data, {
        "source_csv": CSV_PATH,
        "description": "Simplified version with key biographical fields"
    })

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Files created:")
    print(f"  1. {output_path}")
    print(f"  2. {simplified_path}")
    print(f"\nTotal people scraped: {len(results)}")


if __name__ == "__main__":
    main()
