"""Validate list.csv before it is consumed by base_script.py.

Catches the class of mistake that broke the site on 2026-09-09: a stray
character on the header line (`doi,nr_adna_samples#`) silently made
`nr_adna_samples` disappear from every row, because csv.DictReader just
drops unmatched columns instead of erroring out.
"""
import csv
import re
import sys

CSV_FILE = "list.csv"
EXPECTED_HEADER = ["doi", "nr_adna_samples"]
DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$")


def validate(csv_file=CSV_FILE):
    errors = []

    with open(csv_file, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            return [f"{csv_file} is empty."]

        if header != EXPECTED_HEADER:
            errors.append(f"Unexpected header {header!r}, expected {EXPECTED_HEADER!r}.")
            # Header is wrong: don't bother validating rows against it.
            return errors

        seen_dois = {}
        for line_no, row in enumerate(reader, start=2):
            if len(row) != len(EXPECTED_HEADER):
                errors.append(f"Line {line_no}: expected {len(EXPECTED_HEADER)} columns, got {len(row)}: {row!r}")
                continue

            doi, nr_samples = row
            doi_normalized = doi.replace("https://doi.org/", "").strip().lower()

            if not doi_normalized:
                errors.append(f"Line {line_no}: empty doi.")
            elif not DOI_RE.match(doi_normalized):
                errors.append(f"Line {line_no}: doi {doi!r} doesn't look like a valid DOI.")
            elif doi_normalized in seen_dois:
                errors.append(f"Line {line_no}: duplicate doi {doi!r} (first seen on line {seen_dois[doi_normalized]}).")
            else:
                seen_dois[doi_normalized] = line_no

            if not nr_samples.strip().isdigit():
                errors.append(f"Line {line_no}: nr_adna_samples {nr_samples!r} is not a non-negative integer.")

    return errors


if __name__ == "__main__":
    errors = validate()
    if errors:
        sys.stderr.write(f"list.csv validation failed with {len(errors)} error(s):\n")
        for error in errors:
            sys.stderr.write(f"  - {error}\n")
        sys.exit(1)
    print("list.csv looks valid.")
