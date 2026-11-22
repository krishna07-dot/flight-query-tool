"""Flight Schedule Parser and Query Tool - command-line entry point.

Run from the project folder, for example:
    python flight_parser.py -i data/db.csv -a data/airports.txt
"""
import argparse
import glob
import json
import logging
import os
import sys
from datetime import datetime

from csv_loader import parse_files
from validator import load_airports
from query import run_queries


# TODO: fill in your details: plain ASCII, no spaces or underscores.
STUDENT_ID = "241ADB174"
FIRST_NAME = "KRISHNAPRIYA"
LAST_NAME = "KIZHAKKOOTGOPALAKRISHNAN"


class ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(message)


def _write_json(path: str, value) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if not os.path.isdir(parent):
        raise OSError(f"output folder does not exist: {parent}")
    with open(path, "w", encoding="utf-8") as file:
        json.dump(value, file, indent=2)


def _load_json_array(path: str) -> list:
    if not os.path.isfile(path):
        raise FileNotFoundError(f"JSON database does not exist: {path}")
    try:
        with open(path, "r", encoding="utf-8") as file:
            value = json.load(file)
    except json.JSONDecodeError as exc:
        raise ValueError(f"database is not valid JSON: {path}") from exc
    if not isinstance(value, list):
        raise ValueError("database is not a JSON array")
    return value


def _load_queries(path: str):
    if not os.path.isfile(path):
        raise FileNotFoundError(f"query file does not exist: {path}")
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError as exc:
        raise ValueError(f"query file is not valid JSON: {path}") from exc


def main(argv: list[str] | None = None) -> int:
    """Run the whole program and return the exit code (0, 1 or 2)."""
    parser = ArgumentParser(description="Flight Schedule Parser and Query Tool")
    parser.add_argument("-i", "--input")
    parser.add_argument("-d", "--directory")
    parser.add_argument("-j", "--json-db")
    parser.add_argument("-a", "--airports")
    parser.add_argument("-o", "--output")
    parser.add_argument("-q", "--queries")
    parser.add_argument("-r", "--response-folder")

    try:
        args = parser.parse_args(argv)
    except ValueError as exc:
        parser.print_usage(sys.stderr)
        print(f"{parser.prog}: error: {exc}", file=sys.stderr)
        return 2

    sources = sum(value is not None for value in (args.input, args.directory, args.json_db))
    if sources != 1:
        parser.print_usage(sys.stderr)
        print("Error: exactly one data source (-i, -d, or -j) is required", file=sys.stderr)
        return 2

    if args.input or args.directory:
        if not args.airports:
            parser.print_usage(sys.stderr)
            print("Error: -a/--airports is required with -i or -d", file=sys.stderr)
            return 2
    if args.output and args.json_db:
        parser.print_usage(sys.stderr)
        print("Error: -o cannot be used with -j", file=sys.stderr)
        return 2

    logger = logging.getLogger("flight_parser")
    handler = None

    try:
        db = None

        if args.input or args.directory:
            if args.input:
                if not os.path.isfile(args.input):
                    raise FileNotFoundError(f"CSV file does not exist: {args.input}")
                paths = [args.input]
            else:
                if not os.path.isdir(args.directory):
                    raise FileNotFoundError(f"folder does not exist: {args.directory}")
                paths = sorted(
                    path for path in glob.glob(os.path.join(args.directory, "*.csv"))
                    if os.path.isfile(path)
                )
                if not paths:
                    raise ValueError("folder contains no CSV files")

            if not os.path.isfile(args.airports):
                raise FileNotFoundError(f"airport file does not exist: {args.airports}")
            airports = load_airports(args.airports)
            db, errors = parse_files(paths, airports)

            output_path = args.output or os.path.join(os.getcwd(), "db.json")
            _write_json(output_path, db)

            log_path = os.path.join(os.path.dirname(os.path.abspath(output_path)), "errors.log")
            for old_handler in list(logger.handlers):
                logger.removeHandler(old_handler)
                try:
                    old_handler.close()
                except Exception:
                    pass
            handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
            handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s", "%Y-%m-%d %H:%M:%S"))
            logger.addHandler(handler)
            logger.setLevel(logging.WARNING)
            logger.propagate = False
            for message in errors:
                logger.warning(message)
            handler.flush()

        else:
            db = _load_json_array(args.json_db)

        if args.queries:
            queries = _load_queries(args.queries)
            response = run_queries(db, queries)

            response_folder = args.response_folder or os.getcwd()
            if not os.path.isdir(response_folder):
                raise OSError(f"response folder does not exist: {response_folder}")

            now = datetime.now().strftime("%Y%m%d_%H%M")
            response_name = (
                f"response_{STUDENT_ID}_{FIRST_NAME}_{LAST_NAME}_{now}.json"
            )
            response_path = os.path.join(response_folder, response_name)
            _write_json(response_path, response)

        return 0

    except (OSError, ValueError, json.JSONDecodeError, KeyError, TypeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    finally:
        if handler is not None:
            logger.removeHandler(handler)
            handler.close()
        for old_handler in list(logger.handlers):
            logger.removeHandler(old_handler)
            try:
                old_handler.close()
            except Exception:
                pass


if __name__ == "__main__":
    sys.exit(main())
