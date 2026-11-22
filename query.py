
"""Running queries against the flight database."""

from datetime import datetime
import math
import re


RECORD_KEYS = {
    "flight_id",
    "origin",
    "destination",
    "departure_datetime",
    "arrival_datetime",
    "price",
}

DATETIME_PATTERN = re.compile(
    r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}"
)


def valid_datetime(value):
    if not isinstance(value, str):
        return False

    if not DATETIME_PATTERN.fullmatch(value):
        return False

    try:
        datetime.strptime(value, "%Y-%m-%d %H:%M")
        return True
    except ValueError:
        return False


def valid_number(value):
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def run_query(db: list[dict], query: dict) -> dict:
    """Return one response entry for every query object."""

    if not isinstance(query, dict):
        return {
            "query": query,
            "error": "INVALID_QUERY",
            "matches": [],
        }

    allowed_keys = RECORD_KEYS | {
        "min_price",
        "sort_by",
        "order",
        "limit",
    }

    if any(key not in allowed_keys for key in query):
        return {
            "query": query,
            "error": "INVALID_QUERY",
            "matches": [],
        }

    for key in ("flight_id", "origin", "destination"):
        if key in query and not isinstance(query[key], str):
            return {
                "query": query,
                "error": "INVALID_QUERY",
                "matches": [],
            }

    for key in ("departure_datetime", "arrival_datetime"):
        if key in query and not valid_datetime(query[key]):
            return {
                "query": query,
                "error": "INVALID_QUERY",
                "matches": [],
            }

    for key in ("price", "min_price"):
        if key in query and not valid_number(query[key]):
            return {
                "query": query,
                "error": "INVALID_QUERY",
                "matches": [],
            }

    if "sort_by" in query:
        if query["sort_by"] not in RECORD_KEYS:
            return {
                "query": query,
                "error": "INVALID_QUERY",
                "matches": [],
            }

    if "order" in query:
        if (
            "sort_by" not in query
            or query["order"] not in ("asc", "desc")
        ):
            return {
                "query": query,
                "error": "INVALID_QUERY",
                "matches": [],
            }

    if "limit" in query:
        if (
            isinstance(query["limit"], bool)
            or not isinstance(query["limit"], int)
            or query["limit"] < 0
        ):
            return {
                "query": query,
                "error": "INVALID_QUERY",
                "matches": [],
            }

    matches = []

    for flight in db:
        if "flight_id" in query:
            if flight["flight_id"] != query["flight_id"]:
                continue

        if "origin" in query:
            if flight["origin"] != query["origin"]:
                continue

        if "destination" in query:
            if flight["destination"] != query["destination"]:
                continue

        if "departure_datetime" in query:
            if flight["departure_datetime"] < query["departure_datetime"]:
                continue

        if "arrival_datetime" in query:
            if flight["arrival_datetime"] > query["arrival_datetime"]:
                continue

        if "price" in query:
            if flight["price"] > query["price"]:
                continue

        if "min_price" in query:
            if flight["price"] < query["min_price"]:
                continue

        matches.append(flight)

    if "sort_by" in query:
        matches.sort(
            key=lambda flight: flight[query["sort_by"]],
            reverse=query.get("order", "asc") == "desc",
        )

    if "limit" in query:
        matches = matches[:query["limit"]]

    return {
        "query": query,
        "matches": matches,
    }


def run_queries(db: list[dict], queries: dict | list) -> list[dict]:
    """Accept one query object or a list of them; always return a list."""

    if isinstance(queries, dict):
        queries = [queries]

    return [run_query(db, query) for query in queries]
