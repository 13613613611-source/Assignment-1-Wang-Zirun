# Wikipedia Famous People Dataset

A comprehensive biographical dataset containing 97 notable historical figures, scraped from Wikipedia and processed through data cleaning and validation pipelines.

## 📁 Project Structure

```
├── famous_people_wikipedia.json       # Raw scraped data from Wikipedia
├── claened_famous_people_wikipedia.json # Cleaned and normalized data
├── quality_report.txt                  # Data quality validation report
├── famous_people.csv                   # Source CSV with basic metadata
│
├── wikipedia_scraper.py                # Web scraper for Wikipedia infoboxes
├── cleaner.py                          # Data cleaning and normalization script
└── validator.py                       # Data quality validation script
```

## 📊 Dataset Overview

| Metric | Value |
|--------|-------|
| **Total Records** | 97 |
| **Valid Records** | 97 (100%) |
| **Data Source** | Wikipedia API |
| **Categories** | Scientists, Artists, Politicians, Athletes, Writers, Musicians |

### Data Categories Distribution

- **Scientists & Inventors**: 25 (Einstein, Newton, Curie, Tesla, Darwin, etc.)
- **Artists & Musicians**: 20 (Da Vinci, Picasso, Mozart, Van Gogh, etc.)
- **Political Leaders**: 20 (Gandhi, Lincoln, Mandela, Churchill, etc.)
- **Writers & Authors**: 12 (Shakespeare, Tolstoy, Hemingway, etc.)
- **Athletes**: 9 (Messi, Ronaldo, Jordan, Williams, etc.)
- **Philosophers**: 7 (Aristotle, Plato, Socrates, Confucius, etc.)
- **Religious Figures**: 4 (Jesus, Muhammad, Buddha, etc.)

## 📋 Field Documentation

### Required Fields (100% Complete)

| Field | Type | Description |
|-------|------|-------------|
| `wiki_title` | string | Wikipedia article title |
| `wiki_url` | string | Full Wikipedia article URL |

### Recommended Fields

| Field | Completeness | Description |
|-------|-------------|-------------|
| `name` | 100% | Person's full name |
| `description` | 100% | Biographical summary |
| `birth_date` | 96.9% | Date of birth (ISO format: YYYY-MM-DD) |
| `death_date` | 82.5% | Date of death (ISO format: YYYY-MM-DD) |
| `education` | 49.5% | Educational background |
| `spouse` | 62.9% | List of spouses |
| `children` | 53.6% | Names of children |
| `birth_place` | 44.3% | Place of birth |
| `awards` | 44.3% | Notable awards and honors |
| `profession` | 41.2% | Primary profession(s) |
| `known_for` | 39.2% | Key achievements or contributions |
| `citizenship` | 13.4% | Nationality/Citizenship |
| `fields` | 18.6% | Field of work (for scientists) |
| `institutions` | 18.6% | Associated institutions/organizations |

### Optional Fields

| Field | Completeness | Description |
|-------|-------------|-------------|
| `thesis` | 9.3% | Doctoral thesis title |
| `doctoral_advisor` | 8.2% | PhD advisor name |
| `academic_advisor` | 8.2% | Academic mentor(s) |
| `family` | 10.3% | Family information |
| `categories` | 0.0% | Wikipedia categories (not populated) |

## 🔧 Data Processing Pipeline

### 1. Web Scraping (`wikipedia_scraper.py`)

Uses Wikipedia API to extract biographical information from Infobox templates:

```python
# Example usage
python wikipedia_scraper.py
```

**Features:**
- Fetches HTML content via Wikipedia API
- Parses Wikipedia Infobox templates
- Extracts structured biographical data
- Respects rate limits (1 second delay between requests)
- Handles redirects automatically

### 2. Data Cleaning (`cleaner.py`)

Normalizes and cleans raw scraped data:

```python
# Example usage
python cleaner.py
```

**Cleaning Operations:**
- ✅ Removes HTML tags and artifacts
- ✅ Removes reference numbers `[1]`, `[citation needed]`
- ✅ Normalizes pipe-separated values (`|`)
- ✅ Fixes encoding issues (`â€™` → `'`)
- ✅ Standardizes dates to ISO format (YYYY-MM-DD)
- ✅ Extracts location information
- ✅ Cleans spouse/partner lists
- ✅ Removes extra whitespace

### 3. Quality Validation (`validator.py`)

Validates data quality and generates reports:

```python
# Example usage
python validator.py
```

**Validation Checks:**
- ✅ Required field completeness
- ✅ URL format validation
- ✅ Date format validation
- ✅ Content length minimums
- ✅ Encoding issue detection
- ✅ Generates comprehensive quality report

## 📄 Output Files

### `famous_people_wikipedia.json` (Raw)

Original scraped data with full Wikipedia Infobox content.

```json
{
  "generated_at": "2026-02-06T13:43:51Z",
  "count": 97,
  "source": "Wikipedia",
  "data": [
    {
      "name": "Albert Einstein",
      "wiki_title": "Albert Einstein",
      "wiki_url": "https://en.wikipedia.org/wiki/Albert_Einstein",
      "born": "( | 1879-03-14 | ) | 14 March 1879 | Ulm | , | Württemberg | , Germany",
      "birth_date": "( | 1879-03-14 | ) | 14 March 1879 | Ulm | , | Württemberg | , Germany",
      ...
    }
  ]
}
```

### `claened_famous_people_wikipedia.json` (Cleaned)

Normalized and cleaned data ready for analysis.

```json
{
  "generated_at": "2026-02-06T14:00:00Z",
  "count": 97,
  "source": "Wikipedia",
  "description": "Cleaned Wikipedia biographical data",
  "cleaning_applied": [
    "Removed HTML tags and reference numbers",
    "Normalized text encoding for special characters",
    "Standardized dates to ISO format (YYYY-MM-DD)",
    "Removed extra whitespace",
    "Normalized list separators to consistent format"
  ],
  "data": [
    {
      "wiki_title": "Albert Einstein",
      "wiki_url": "https://en.wikipedia.org/wiki/Albert_Einstein",
      "birth_date": "1879-03-14",
      "birth_place": "Ulm , Württemberg , Germany",
      "death_date": "1955-04-18",
      "spouse": ["Mileva Marić", "Elsa Löwenthal"],
      "description": "Albert Einstein was a German-born theoretical physicist...",
      ...
    }
  ]
}
```

### `quality_report.txt`

Human-readable quality assessment report.

```
======================================================================
WIKIPEDIA DATA QUALITY REPORT
======================================================================

Total records processed:     97
Valid records:               97 (100.0%)
Invalid records:             0 (0.0%)

FIELD COMPLETENESS
----------------------------------------------------------------------
Field                        Present    Missing          %
wiki_title    [REQUIRED]         97          0     100.0%
wiki_url      [REQUIRED]         97          0     100.0%
name          [RECOMMENDED]         97          0     100.0%
description   [RECOMMENDED]         97          0     100.0%
birth_date    [RECOMMENDED]         94          3      96.9%
...
```

## 📈 Sample Data

### Notable Scientists
| Name | Birth Date | Death Date | Known For |
|------|------------|------------|-----------|
| Albert Einstein | 1879-03-14 | 1955-04-18 | Theory of Relativity |
| Isaac Newton | 1643-01-04 | 1727-03-31 | Laws of Motion |
| Marie Curie | 1867-11-07 | 1934-07-04 | Radioactivity |
| Nikola Tesla | 1856-07-10 | 1943-01-07 | AC Electricity |
| Charles Darwin | 1809-02-12 | 1882-04-19 | Theory of Evolution |

### Notable Artists
| Name | Birth Date | Death Date | Known For |
|------|------------|------------|-----------|
| Leonardo da Vinci | 1452-04-15 | 1519-05-02 | Mona Lisa |
| Vincent van Gogh | 1853-03-30 | 1890-07-29 | Starry Night |
| Michelangelo | 1475-03-06 | 1564-02-18 | Sistine Chapel |
| Frida Kahlo | 1907-07-06 | 1954-07-13 | Self-portraits |

### Notable Political Leaders
| Name | Birth Date | Death Date | Known For |
|------|------------|------------|-----------|
| Mahatma Gandhi | 1869-10-02 | 1948-01-30 | Indian Independence |
| Nelson Mandela | 1918-07-18 | 2013-12-05 | Anti-Apartheid |
| Winston Churchill | 1874-11-30 | 1965-01-24 | WWII Leadership |
| Abraham Lincoln | 1809-02-12 | 1865-04-15 | Emancipation Proclamation |

## 🚀 Usage Examples

### Python

```python
import json

# Load cleaned data
with open('claened_famous_people_wikipedia.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Access individual records
for person in data['data']:
    print(f"{person['wiki_title']}: {person.get('birth_date', 'N/A')}")
```

### Command Line

```bash
# Re-run scraper
python wikipedia_scraper.py

# Re-run cleaner
python cleaner.py

# Re-run validator
python validator.py
```

## 📝 Notes

- **Date Format**: All dates standardized to ISO 8601 format (YYYY-MM-DD)
- **Missing Data**: Some fields have lower completeness rates due to:
  - Ancient historical figures (limited birth/death records)
  - Living individuals (no death date)
  - Wikipedia infobox variations across different article types
- **Encoding**: Special characters (umlauts, accents) are properly preserved
- **Rate Limiting**: Scraper respects Wikipedia's API rate limits

## 📅 Data Generation

- **Scraped**: 2026-02-06
- **Cleaned**: 2026-02-06
- **Validated**: 2026-02-06
- **Total Processing Time**: ~2 minutes (97 records with 1s delay)

## 🔗 References

- Wikipedia API: https://en.wikipedia.org/w/api.php
- Data scraped from: https://en.wikipedia.org/wiki/Main_Page

## 📄 License

This dataset is generated for educational and research purposes using publicly available Wikipedia data.

