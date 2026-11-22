"""Row validation: airport list loading, single-row checks, record building."""
import math
import re
from datetime import datetime


def load_airports(path: str) -> set[str]:
    """Read an airport list file and return the set of codes.

    One code per line. Strip whitespace; skip blank lines and lines
    starting with '#'.
    """
    airports = set()

    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            code = line.strip()
            if code and not code.startswith("#"):
                airports.add(code)

    return airports

def validate_row(fields: list[str], airports: set[str]) -> str | None:
    """Check one CSV row (fields as returned by csv.reader, not yet stripped).

    Return None if the row is valid, otherwise the error code of the
    FIRST failing check (checks 1-11 in the specification, in order).
    Does not check for duplicates.
    """
    fields = [field.strip() for field in fields]

    if len(fields) != 6:
        return "WRONG_FIELD_COUNT"

    if any(field == "" for field in fields):
        return "MISSING_FIELD"

    flight_id, origin, destination, departure, arrival, price = fields

    if not re.fullmatch(r"[A-Z0-9]{2,8}", flight_id):
        return "INVALID_FLIGHT_ID"

    if not re.fullmatch(r"[A-Z]{3}", origin) or origin not in airports:
        return "INVALID_ORIGIN"

    if not re.fullmatch(r"[A-Z]{3}", destination) or destination not in airports:
        return "INVALID_DESTINATION"

    if origin == destination:
        return "SAME_ORIGIN_DESTINATION"

    date_format = "%Y-%m-%d %H:%M"
    date_pattern = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}"

    if not re.fullmatch(date_pattern, departure):
        return "INVALID_DEPARTURE"

    try:
        departure_time = datetime.strptime(departure, date_format)
    except ValueError:
        return "INVALID_DEPARTURE"

    if not re.fullmatch(date_pattern, arrival):
        return "INVALID_ARRIVAL"

    try:
        arrival_time = datetime.strptime(arrival, date_format)
    except ValueError:
        return "INVALID_ARRIVAL"

    if arrival_time <= departure_time:
        return "ARRIVAL_NOT_AFTER_DEPARTURE"

    try:
        flight_price = float(price)
    except ValueError:
        return "INVALID_PRICE"

    if not math.isfinite(flight_price):
        return "INVALID_PRICE"

    if flight_price <= 0:
        return "NON_POSITIVE_PRICE"

    return None

def to_record(fields: list[str]) -> dict:
    """Turn a valid row into a flight record dictionary.

    Keys: flight_id, origin, destination, departure_datetime,
    arrival_datetime (stripped strings) and price (float).
    """
    return {
        "flight_id": fields[0].strip(),
        "origin": fields[1].strip(),
        "destination": fields[2].strip(),
        "departure_datetime": fields[3].strip(),
        "arrival_datetime": fields[4].strip(),
        "price": float(fields[5].strip())
    }