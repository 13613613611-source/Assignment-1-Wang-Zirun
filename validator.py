# Wikipedia Data Validator
# Validate and quality check scraped Wikipedia biographical data

import json
import re
import os
from collections import defaultdict
from datetime import datetime
from typing import Optional


class WikipediaValidator:
    """Validate Wikipedia biographical data for quality assurance."""

    def __init__(self):
        self.validation_results = []
        self.field_completeness = defaultdict(int)
        self.total_records = 0
        self.common_failures = defaultdict(int)

        # Required and optional fields with their validation rules
        self.field_rules = {
            "required": {
                "wiki_title": {"min_length": 1, "max_length": 500},
                "wiki_url": {"min_length": 10, "pattern": r'^https?://'},
            },
            "recommended": {
                "name": {"min_length": 1, "max_length": 300},
                "description": {"min_length": 50},
                "birth_date": {"min_length": 4, "max_length": 20},
                "death_date": {"min_length": 4, "max_length": 20},
                "birth_place": {"min_length": 2},
                "death_place": {"min_length": 2},
                "profession": {"min_length": 2},
                "citizenship": {"min_length": 2},
                "known_for": {"min_length": 5},
                "fields": {"min_length": 2},
                "education": {"min_length": 5},
                "spouse": {"is_list": True, "min_count": 0},
                "children": {"min_length": 0},
                "awards": {"min_length": 5},
                "institutions": {"min_length": 5},
                "thesis": {"min_length": 5},
                "doctoral_advisor": {"min_length": 5},
            },
            "optional": {
                "categories": {"is_list": True},
                "family": {"min_length": 2},
                "academic_advisor": {"min_length": 5},
            }
        }

    def validate_url(self, url: str) -> tuple[bool, Optional[str]]:
        """Validate URL format."""
        if not url:
            return False, "URL is empty"

        url = str(url).strip()

        # Check basic URL format
        if not re.match(r'^https?://', url):
            return False, f"Invalid URL format: {url}"

        # Check for valid domain
        if not re.match(r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', url):
            return False, f"URL has invalid domain: {url}"

        # Check for common issues
        if ' ' in url:
            return False, "URL contains spaces"

        if url.count('//') > 1:
            return False, "URL has multiple protocol indicators"

        return True, None

    def validate_date(self, date_str: str) -> tuple[bool, Optional[str]]:
        """Validate date format."""
        if not date_str:
            return True, None  # Empty dates are OK for optional fields

        date_str = str(date_str).strip()

        # ISO format
        if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            return True, None

        # Year only (BC dates)
        if re.match(r'^-\d{4}$', date_str):
            return True, None

        # Year range (for birth/death)
        if re.match(r'^\d{4}\s+to\s+\d{4}$', date_str):
            return True, None

        # Unknown dates marked with ?
        if re.match(r'^\d{4}-\?\?-\?\?$', date_str):
            return True, None

        # Common human-readable formats
        readable_formats = [
            r'^\d{1,2}\s+\w+\s+\d{4}$',  # 14 March 1879
            r'^\w+\s+\d{1,2},?\s+\d{4}$',  # March 14, 1879
            r'^\d{4}$',  # Just year
        ]

        for fmt in readable_formats:
            if re.match(fmt, date_str):
                return True, None

        # Partial dates
        if re.match(r'^\d{4}-\d{2}$', date_str):
            return True, None

        return False, f"Invalid date format: {date_str}"

    def validate_field_length(self, value: str, field: str, rules: dict) -> tuple[bool, Optional[str]]:
        """Validate field content length."""
        if value is None:
            return True, None

        str_value = str(value).strip()

        # Handle lists
        if rules.get("is_list"):
            if isinstance(value, list):
                min_count = rules.get("min_count", 0)
                if len(value) < min_count:
                    return False, f"List has insufficient items: {len(value)} < {min_count}"
                return True, None
            else:
                # Convert to string and validate
                str_value = str(value)

        min_length = rules.get("min_length", 0)
        max_length = rules.get("max_length", float('inf'))

        if len(str_value) < min_length:
            return False, f"Field too short: {len(str_value)} < {min_length}"

        if len(str_value) > max_length:
            return False, f"Field too long: {len(str_value)} > {max_length}"

        return True, None

    def validate_record(self, record: dict, index: int) -> dict:
        """Validate a single record and return validation result."""
        self.total_records += 1
        result = {
            "index": index,
            "wiki_title": record.get("wiki_title", ""),
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "field_status": {}
        }

        # Check required fields
        for field, rules in self.field_rules["required"].items():
            value = record.get(field, "")
            self.field_completeness[field] += 1 if value else 0

            if not value:
                result["is_valid"] = False
                result["errors"].append(f"Missing required field: {field}")
                self.common_failures["missing_required"] += 1
                result["field_status"][field] = "missing"
                continue

            # Validate URL format
            if field == "wiki_url":
                is_valid, error = self.validate_url(value)
                if not is_valid:
                    result["is_valid"] = False
                    result["errors"].append(error)
                    self.common_failures["invalid_url"] += 1
                    result["field_status"][field] = "invalid"
                else:
                    result["field_status"][field] = "valid"
            else:
                result["field_status"][field] = "valid"

        # Check recommended fields
        for field, rules in self.field_rules["recommended"].items():
            value = record.get(field, "")
            is_present = bool(value and (not isinstance(value, str) or value.strip()))

            if is_present:
                self.field_completeness[field] += 1

                # Validate length
                is_valid, error = self.validate_field_length(value, field, rules)
                if not is_valid:
                    result["warnings"].append(f"{field}: {error}")

                result["field_status"][field] = "present"
            else:
                result["field_status"][field] = "missing"

        # Check optional fields
        for field in self.field_rules["optional"]:
            value = record.get(field, "")
            if value:
                self.field_completeness[field] += 1
                result["field_status"][field] = "present"
            else:
                result["field_status"][field] = "not_present"

        # Additional content checks
        description = record.get("description", "")
        if description and len(description) < 50:
            result["warnings"].append("Description is very short (< 50 characters)")
            self.common_failures["short_description"] += 1

        # Check for encoding issues
        text_fields = ["name", "description", "known_for"]
        for field in text_fields:
            value = record.get(field, "")
            if value and isinstance(value, str):
                # Check for common encoding artifacts
                if 'Ã' in value or 'â' in value:
                    result["warnings"].append(f"{field}: Possible encoding issues detected")
                    self.common_failures["encoding_issues"] += 1

        return result

    def generate_report(self, validation_results: list[dict]) -> str:
        """Generate a comprehensive quality report."""
        report = []
        report.append("=" * 70)
        report.append("WIKIPEDIA DATA QUALITY REPORT")
        report.append(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        report.append("=" * 70)
        report.append("")

        # Summary statistics
        valid_count = sum(1 for r in validation_results if r["is_valid"])
        invalid_count = len(validation_results) - valid_count
        valid_percentage = (valid_count / len(validation_results) * 100) if validation_results else 0

        report.append("-" * 70)
        report.append("SUMMARY")
        report.append("-" * 70)
        report.append(f"Total records processed:     {len(validation_results)}")
        report.append(f"Valid records:               {valid_count} ({valid_percentage:.1f}%)")
        report.append(f"Invalid records:             {invalid_count} ({100-valid_percentage:.1f}%)")
        report.append("")

        # Field completeness
        report.append("-" * 70)
        report.append("FIELD COMPLETENESS")
        report.append("-" * 70)

        all_fields = (
            list(self.field_rules["required"].keys()) +
            list(self.field_rules["recommended"].keys()) +
            list(self.field_rules["optional"].keys())
        )

        report.append(f"{'Field':<25} {'Present':>10} {'Missing':>10} {'%':>10}")
        report.append("-" * 60)

        for field in all_fields:
            present = self.field_completeness.get(field, 0)
            missing = self.total_records - present
            percentage = (present / self.total_records * 100) if self.total_records > 0 else 0

            if field in self.field_rules["required"]:
                status = "[REQUIRED]"
            elif field in self.field_rules["recommended"]:
                status = "[RECOMMENDED]"
            else:
                status = "[OPTIONAL]"

            report.append(f"{field:<25} {status:<10} {present:>10} {missing:>10} {percentage:>9.1f}%")

        report.append("")

        # Common validation failures
        if self.common_failures:
            report.append("-" * 70)
            report.append("COMMON VALIDATION FAILURES")
            report.append("-" * 70)

            sorted_failures = sorted(self.common_failures.items(), key=lambda x: x[1], reverse=True)
            for failure_type, count in sorted_failures:
                report.append(f"  {failure_type:<40}: {count:>5} occurrences")

            report.append("")

        # Invalid records detail
        invalid_records = [r for r in validation_results if not r["is_valid"]]
        if invalid_records:
            report.append("-" * 70)
            report.append("INVALID RECORDS DETAIL")
            report.append("-" * 70)

            for record in invalid_records[:20]:  # Limit to first 20 for readability
                report.append(f"\nRecord #{record['index']}: {record['wiki_title']}")
                report.append("  Errors:")
                for error in record["errors"]:
                    report.append(f"    - {error}")
                if record["warnings"]:
                    report.append("  Warnings:")
                    for warning in record["warnings"]:
                        report.append(f"    - {warning}")

            if len(invalid_records) > 20:
                report.append(f"\n... and {len(invalid_records) - 20} more invalid records")

        report.append("")
        report.append("=" * 70)
        report.append("END OF REPORT")
        report.append("=" * 70)

        return "\n".join(report)

    def validate_all(self, data: list[dict]) -> list[dict]:
        """Validate all records in the dataset."""
        results = []
        for i, record in enumerate(data):
            result = self.validate_record(record, i)
            results.append(result)
        return results


def load_json(path: str) -> dict:
    """Load JSON data from file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    """Main function to run validation."""
    RAW_INPUT_PATH = r"C:\Users\11613\Desktop\1\2026\2月\FF-260205\DATA2\famous_people_wikipedia.json"
    CLEANED_INPUT_PATH = r"C:\Users\11613\Desktop\1\2026\2月\FF-260205\DATA2\claened_famous_people_wikipedia.json"
    OUTPUT_PATH = r"C:\Users\11613\Desktop\1\2026\2月\FF-260205\DATA2\quality_report.txt"

    print("=" * 60)
    print("Wikipedia Data Validator")
    print("=" * 60)

    # Try cleaned data first, then raw data
    input_path = CLEANED_INPUT_PATH
    data_source = "cleaned"

    if not os.path.exists(CLEANED_INPUT_PATH):
        if os.path.exists(RAW_INPUT_PATH):
            input_path = RAW_INPUT_PATH
            data_source = "raw"
        else:
            print(f"Error: Neither cleaned nor raw data file found!")
            print(f"  Checked: {CLEANED_INPUT_PATH}")
            print(f"  Checked: {RAW_INPUT_PATH}")
            return

    print(f"\nLoading data from: {input_path}")
    with open(input_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    records = raw_data.get('data', raw_data)
    print(f"Loaded {len(records)} records from {data_source} data")

    # Validate
    print("\nValidating records...")
    validator = WikipediaValidator()
    validation_results = validator.validate_all(records)

    # Generate report
    report = validator.generate_report(validation_results)

    # Save report
    print(f"\nSaving report to: {OUTPUT_PATH}")
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(report)

    # Print summary
    print("\n" + "=" * 60)
    print("VALIDATION COMPLETE")
    print("=" * 60)
    valid_count = sum(1 for r in validation_results if r["is_valid"])
    print(f"Total records: {len(validation_results)}")
    print(f"Valid: {valid_count}")
    print(f"Invalid: {len(validation_results) - valid_count}")
    print(f"\nFull report saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
