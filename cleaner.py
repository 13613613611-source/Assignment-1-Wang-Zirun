# Wikipedia Data Cleaner
# Clean and normalize scraped Wikipedia biographical data

import json
import re
import os
from datetime import datetime
from typing import Optional


class WikipediaDataCleaner:
    """Clean and normalize Wikipedia biographical data."""

    def __init__(self):
        # Month name mappings
        self.month_map = {
            "january": "01", "february": "02", "march": "03", "april": "04",
            "may": "05", "june": "06", "july": "07", "august": "08",
            "september": "09", "october": "10", "november": "11", "december": "12",
            "jan": "01", "feb": "02", "mar": "03", "apr": "04",
            "jun": "06", "jul": "07", "aug": "08", "sep": "09", "oct": "10",
            "nov": "11", "dec": "12",
            "january ": "01", "february ": "02", "march ": "03", "april ": "04",
            "may ": "05", "june ": "06", "july ": "07", "august ": "08",
            "september ": "09", "october ": "10", "november ": "11", "december ": "12",
        }

    def clean_text(self, text: str) -> str:
        """Remove extra whitespace, HTML artifacts, and normalize text."""
        if not text:
            return ""

        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)

        # Remove reference numbers like [1], [2], etc.
        text = re.sub(r'\[\d+\]', '', text)
        text = re.sub(r'\[\w+\]', '', text)  # Also remove [citation needed] etc.

        # Remove pipe separators used in Wikipedia tables - BEFORE cleaning
        text = re.sub(r'\s*\|\s*', ' ', text)

        # Remove parentheses and their content (like "(aged XX)" or "(...)")
        # Keep location parentheses if they contain commas (likely part of address)
        text = re.sub(r'\s*\([^)]*\)\s*', ' ', text)

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

        # Remove leading/trailing punctuation artifacts
        text = re.sub(r'^[\s,\.:;()]+|[\s,\.:;()]+$', '', text)

        return text

    def extract_date_from_text(self, text: str) -> Optional[str]:
        """Extract the most likely date from mixed text."""
        if not text:
            return None

        # Try to find ISO date first (YYYY-MM-DD) - BEFORE cleaning
        iso_match = re.search(r'(\d{4}-\d{2}-\d{2})', text)
        if iso_match:
            return iso_match.group(1)

        # Clean the text first
        cleaned = self.clean_text(text)

        # Try to parse various date formats
        parsed = self.parse_date(cleaned)
        if parsed and re.match(r'\d{4}-\d{2}-\d{2}', parsed):
            return parsed

        return None

    def extract_location_from_text(self, text: str) -> str:
        """Extract location from mixed text (remove dates)."""
        if not text:
            return ""

        text = self.clean_text(text)

        # Remove common date patterns at the beginning
        # Patterns like "14 March 1879", "March 14, 1879", etc.
        date_patterns = [
            r'^\d{1,2}\s+\w+\s+\d{4}\s*',      # "14 March 1879"
            r'^\w+\s+\d{1,2},?\s+\d{4}\s*',     # "March 14, 1879"
            r'^\d{4}-\d{2}-\d{2}\s*',           # "1879-03-14"
        ]

        for pattern in date_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)

        # Remove "(aged XX)" patterns
        text = re.sub(r'\(aged\s*\d+\)', '', text)

        # Remove any remaining standalone 4-digit years
        text = re.sub(r'\s+\d{4}\s*$', '', text)
        text = re.sub(r'^\s*\d{4}\s*', '', text)

        # Clean up extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        # Remove leading/trailing commas and spaces
        text = re.sub(r'^[\s,]+|[\s,]+$', '', text)

        return text

    def clean_record(self, record: dict) -> dict:
        """Clean a single person's record."""
        cleaned = {}

        # Copy and clean basic fields
        basic_fields = ['name', 'wiki_title', 'wiki_url', 'description']
        for field in basic_fields:
            if field in record:
                value = record[field]
                if isinstance(value, str):
                    cleaned[field] = self.clean_text(self.normalize_encoding(value))
                else:
                    cleaned[field] = value

        # Handle born field - extract date and place
        if 'born' in record:
            born_value = record['born']

            # Extract ISO date first
            iso_date = self.extract_date_from_text(born_value)
            cleaned['birth_date'] = iso_date if iso_date else self.clean_text(born_value)

            # Try to extract birth place from description field or original born field
            birth_place = record.get('birth_place', '')
            if birth_place:
                cleaned['birth_place'] = self.extract_location_from_text(birth_place)
            else:
                # Try to extract place from born value
                cleaned['birth_place'] = self.extract_location_from_text(born_value)

        # Handle died field - extract date and place
        if 'died' in record:
            died_value = record['died']

            # Extract ISO date first
            iso_date = self.extract_date_from_text(died_value)
            cleaned['death_date'] = iso_date if iso_date else self.clean_text(died_value)

            # Extract death place
            death_place = record.get('death_place', '')
            if death_place:
                cleaned['death_place'] = self.extract_location_from_text(death_place)
            else:
                cleaned['death_place'] = self.extract_location_from_text(died_value)

    def normalize_encoding(self, text: str) -> str:
        """Normalize text encoding for special characters."""
        if not text:
            return ""

        # Fix common encoding issues
        replacements = {
            'Ã¼': 'ü', 'Ã¼': 'ü', 'Ã±': 'ñ', 'Ã©': 'é',
            'Ã ': 'à', 'Ã¨': 'è', 'Ã¢': 'â', 'Ã®': 'î',
            'Ã´': 'ô', 'Ã»': 'û', 'Ã§': 'ç', 'Ã‰': 'É',
            'â€™': "'",  # Right single quote
            'â€˜': "'",  # Left single quote
            'â€"': '"',  # Em dash
            'â€': '"',   # Left double quote
            'â€': '"',   # Right double quote
            'â€¦': '...',  # Ellipsis
            '\xa0': ' ',  # Non-breaking space
            '\u200b': '',  # Zero-width space
            '\u200c': '',  # Zero-width non-joiner
            '\u200d': '',  # Zero-width joiner
            '\u2013': '-',  # En dash
            '\u2014': '—',  # Em dash
            '\u2018': "'",  # Left single quote
            '\u2019': "'",  # Right single quote
            '\u201c': '"',  # Left double quote
            '\u201d': '"',  # Right double quote
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        return text

    def parse_date(self, date_str: str) -> Optional[str]:
        """Parse various date formats and return ISO format (YYYY-MM-DD)."""
        if not date_str:
            return None

        date_str = self.clean_text(date_str)
        date_str = self.normalize_encoding(date_str)

        # Handle BC/BCE dates
        bc_adjustment = 1
        if 'bc' in date_str.lower() or 'bce' in date_str.lower():
            bc_adjustment = -1
            date_str = re.sub(r'\s*(bc|bce|BC|BCE)\s*', '', date_str)

        # Remove parentheses content (locations)
        date_str = re.sub(r'\s*\([^)]*\)', '', date_str)
        date_str = date_str.strip()

        # Try various date formats
        formats = [
            '%d %B %Y',    # 14 March 1879
            '%d %b %Y',    # 14 Mar 1879
            '%B %d, %Y',   # March 14, 1879
            '%B %d %Y',    # March 14 1879
            '%Y-%m-%d',    # 1879-03-14
            '%d/%m/%Y',    # 14/03/1879
            '%m/%d/%Y',    # 03/14/1879
            '%Y',          # Just year
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                year = dt.year * bc_adjustment
                return f"{year:04d}-{dt.month:02d}-{dt.day:02d}"
            except ValueError:
                continue

        # Handle month name at start (e.g., "March 1879" -> "1879-03-??")
        month_match = re.match(r'(\w+)\s*(\d{4})', date_str)
        if month_match:
            month_name = month_match.group(1).lower()
            year = int(month_match.group(2)) * bc_adjustment
            if month_name in self.month_map:
                return f"{year:04d}-{self.month_map[month_name]}-??"

        # Handle just year
        year_match = re.match(r'^(\d{4})$', date_str)
        if year_match:
            year = int(year_match.group(1)) * bc_adjustment
            return f"{year:04d}-??-??"

        # Handle year range like "1879–1955"
        year_range = re.match(r'^(\d{4}).*?(\d{4})$', date_str)
        if year_range:
            start = int(year_range.group(1)) * bc_adjustment
            end = int(year_range.group(2)) * bc_adjustment
            return f"{start:04d} to {end:04d}"

        return date_str

    def clean_date_field(self, value: str) -> str:
        """Clean and standardize a date field value."""
        if not value:
            return ""

        # Handle date ranges with ages like "18 April 1955 (aged 76)"
        # Extract just the date part
        date_match = re.match(r'^([^(]+)', value)
        if date_match:
            value = date_match.group(1).strip()

        # Parse to ISO format
        iso_date = self.parse_date(value)
        if iso_date:
            return iso_date

        # Fallback: just clean the text
        return self.clean_text(value)

    def clean_list_value(self, value: str) -> list:
        """Clean a pipe-separated list value into a list."""
        if not value:
            return []

        # Clean the text
        cleaned = self.clean_text(self.normalize_encoding(value))

        # Split by common separators
        items = re.split(r'\s*\|\s*|\s*,\s*', cleaned)
        items = [item.strip() for item in items if item.strip()]
        items = list(dict.fromkeys(items))  # Remove duplicates while preserving order

        return items

    def clean_record(self, record: dict) -> dict:
        """Clean a single person's record."""
        cleaned = {}

        # Copy and clean basic fields
        basic_fields = ['name', 'wiki_title', 'wiki_url', 'description']
        for field in basic_fields:
            if field in record:
                value = record[field]
                if isinstance(value, str):
                    cleaned[field] = self.clean_text(self.normalize_encoding(value))
                else:
                    cleaned[field] = value

        # Handle born field - extract date and place
        if 'born' in record:
            born_value = record['born']

            # Extract ISO date first
            iso_date = self.extract_date_from_text(born_value)
            cleaned['birth_date'] = iso_date if iso_date else self.clean_text(born_value)

            # Try to extract birth place from description field or original born field
            birth_place = record.get('birth_place', '')
            if birth_place:
                cleaned['birth_place'] = self.extract_location_from_text(birth_place)
            else:
                # Try to extract place from born value
                cleaned['birth_place'] = self.extract_location_from_text(born_value)

        # Handle died field - extract date and place
        if 'died' in record:
            died_value = record['died']

            # Extract ISO date first
            iso_date = self.extract_date_from_text(died_value)
            cleaned['death_date'] = iso_date if iso_date else self.clean_text(died_value)

            # Extract death place
            death_place = record.get('death_place', '')
            if death_place:
                cleaned['death_place'] = self.extract_location_from_text(death_place)
            else:
                cleaned['death_place'] = self.extract_location_from_text(died_value)

        # Handle spouse (may be a list)
        if 'spouse' in record:
            spouses = record['spouse']
            if isinstance(spouses, list):
                # Clean each spouse entry and remove empty ones
                cleaned_spouses = []
                current_spouse = ""
                for s in spouses:
                    if isinstance(s, str):
                        s_clean = self.clean_text(self.normalize_encoding(s))
                        # Check if this looks like a name (contains letters and no year patterns)
                        # Skip entries that are just years or common separators
                        if re.match(r'^\d{4}', s_clean):
                            continue
                        if s_clean in ['m', 'div', '', 'married', 'died']:
                            continue
                        # Check if this looks like a person's name
                        if len(s_clean) > 3 and any(c.isalpha() for c in s_clean):
                            if current_spouse:
                                # Complete previous spouse entry
                                cleaned_spouses.append(current_spouse.strip())
                            current_spouse = s_clean
                        elif s_clean and current_spouse:
                            # Append year info to current spouse
                            current_spouse += " " + s_clean

                if current_spouse.strip():
                    cleaned_spouses.append(current_spouse.strip())

                cleaned['spouse'] = cleaned_spouses
            elif isinstance(spouses, str):
                cleaned['spouse'] = self.clean_list_value(spouses)
            else:
                cleaned['spouse'] = []

        # Handle other text fields
        text_fields = [
            'citizenship', 'education', 'profession', 'known_for',
            'children', 'family', 'awards', 'fields', 'institutions',
            'thesis', 'doctoral_advisor', 'academic_advisor'
        ]

        for field in text_fields:
            if field in record:
                value = record[field]
                if isinstance(value, str):
                    cleaned[field] = self.clean_text(self.normalize_encoding(value))
                elif isinstance(value, list):
                    cleaned[field] = [
                        self.clean_text(self.normalize_encoding(str(v)))
                        for v in value if v
                    ]
                else:
                    cleaned[field] = ""

        # Clean categories
        if 'categories' in record:
            cleaned['categories'] = [
                self.clean_text(self.normalize_encoding(c))
                for c in record['categories'] if c
            ]

        return cleaned

    def clean_all(self, data: list[dict]) -> list[dict]:
        """Clean all records in the dataset."""
        cleaned_records = []
        for record in data:
            cleaned_record = self.clean_record(record)
            cleaned_records.append(cleaned_record)
        return cleaned_records


def load_json(path: str) -> dict:
    """Load JSON data from file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(path: str, data: dict) -> None:
    """Save data to JSON file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    """Main function to clean Wikipedia data."""
    INPUT_PATH = r"C:\Users\11613\Desktop\1\2026\2月\FF-260205\DATA2\famous_people_wikipedia.json"
    OUTPUT_PATH = r"C:\Users\11613\Desktop\1\2026\2月\FF-260205\DATA2\claened_famous_people_wikipedia.json"

    print("=" * 60)
    print("Wikipedia Data Cleaner")
    print("=" * 60)

    # Load data
    print(f"\nLoading data from: {INPUT_PATH}")
    with open(INPUT_PATH, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    records = raw_data.get('data', raw_data)
    print(f"Loaded {len(records)} records")

    # Clean data
    print("\nCleaning data...")
    cleaner = WikipediaDataCleaner()
    cleaned_records = cleaner.clean_all(records)

    # Save cleaned data
    print(f"\nSaving cleaned data to: {OUTPUT_PATH}")
    output = {
        "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "Wikipedia",
        "count": len(cleaned_records),
        "description": "Cleaned Wikipedia biographical data",
        "cleaning_applied": [
            "Removed HTML tags and reference numbers",
            "Normalized text encoding for special characters",
            "Standardized dates to ISO format (YYYY-MM-DD)",
            "Removed extra whitespace",
            "Normalized list separators to consistent format"
        ],
        "data": cleaned_records
    }
    save_json(OUTPUT_PATH, output)

    # Print summary
    print("\n" + "=" * 60)
    print("CLEANING SUMMARY")
    print("=" * 60)
    print(f"Input:  {INPUT_PATH}")
    print(f"Output: {OUTPUT_PATH}")
    print(f"Records processed: {len(cleaned_records)}")

    # Show sample of cleaned data
    print("\n" + "-" * 60)
    print("Sample cleaned records:")
    print("-" * 60)

    for i, record in enumerate(cleaned_records[:3], 1):
        print(f"\n{i}. {record.get('wiki_title', 'Unknown')}")
        if 'birth_date' in record:
            print(f"   Birth: {record.get('birth_date', 'N/A')}")
        if 'death_date' in record:
            print(f"   Death: {record.get('death_date', 'N/A')}")
        if 'birth_place' in record:
            print(f"   Birth Place: {record.get('birth_place', 'N/A')}")
        if 'death_place' in record:
            print(f"   Death Place: {record.get('death_place', 'N/A')}")


if __name__ == "__main__":
    main()
