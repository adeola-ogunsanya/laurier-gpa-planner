"""
storage.py - Saves and loads data as JSON files so nothing is lost
when the program closes.
"""

import json
import os

# Keep the data files next to this script, so it works no matter where
# it's run from (a terminal, Eclipse, VS Code, ...).
FOLDER = os.path.dirname(os.path.abspath(__file__))
COURSES_FILE = os.path.join(FOLDER, "my_courses.json")
CATALOG_FILE = os.path.join(FOLDER, "catalog.json")


def load_json(path, default):
    """Read a JSON file. If it doesn't exist yet, return `default`."""
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json(path, data):
    """Write data to a JSON file (pretty-printed so it's easy to read)."""
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def load_courses():
    return load_json(COURSES_FILE, [])


def save_courses(courses):
    save_json(COURSES_FILE, courses)


def load_catalog():
    return load_json(CATALOG_FILE, {})
