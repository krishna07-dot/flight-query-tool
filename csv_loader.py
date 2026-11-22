
"""Reading CSV files into flight records and error messages."""

import csv
import os
from validator import validate_row, to_record


def parse_files(paths: list[str], airports: set[str]) -> tuple[list[dict], list[str]]:
    """Process the CSV files in the order given."""

    records = []
    errors = []
    seen_flights = set()

    for path in paths:
        filename = os.path.basename(path)

        with open(path, "r", encoding="utf-8", newline="") as file:
            for line_number, line in enumerate(file, start=1):

                if line_number == 1:
                    continue

                if not line.strip() or line.lstrip().startswith("#"):
                    continue

                try:
                    fields = next(csv.reader([line]))
                except csv.Error:
                    errors.append(
                        f"{filename}:{line_number}: WRONG_FIELD_COUNT | {line.rstrip()}"
                    )
                    continue

                fields = [field.strip() for field in fields]

                error_code = validate_row(fields, airports)

                if error_code is not None:
                    errors.append(
                        f"{filename}:{line_number}: {error_code} | {line.rstrip()}"
                    )
                    continue

                flight_id = fields[0]
                departure = fields[3]
                duplicate_key = (flight_id, departure)

                if duplicate_key in seen_flights:
                    errors.append(
                        f"{filename}:{line_number}: DUPLICATE_FLIGHT | {line.rstrip()}"
                    )
                    continue

                seen_flights.add(duplicate_key)
                records.append(to_record(fields))

    return records, errors
