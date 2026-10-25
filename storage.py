"""
storage.py - Saves and loads data as JSON files so nothing is lost
when the program closes.
"""

import json
import os

COURSES_FILE = "my_courses.json"
CATALOG_FILE = "catalog.json"


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


def load_courses(path=COURSES_FILE):
    return load_json(path, [])


def save_courses(courses, path=COURSES_FILE):
    save_json(path, courses)


def load_catalog(path=CATALOG_FILE):
    return load_json(path, {})
