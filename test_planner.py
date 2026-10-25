"""
Tests - run with:  python -m pytest
(install pytest first with:  pip install pytest)
"""

import pytest

from grades import (calculate_gpa, grade_to_points, percent_to_letter,
                    points_needed_for_target)
from prereqs import check_prereqs, eligible_courses


# ----- grade conversion -----

def test_percent_boundaries():
    assert percent_to_letter(100) == "A+"
    assert percent_to_letter(90) == "A+"
    assert percent_to_letter(89) == "A"
    assert percent_to_letter(80) == "A-"
    assert percent_to_letter(50) == "D-"
    assert percent_to_letter(49) == "F"


def test_grade_to_points_accepts_percent_or_letter():
    assert grade_to_points(84) == 10
    assert grade_to_points("84") == 10
    assert grade_to_points("a-") == 10
    assert grade_to_points("F") == 0


def test_invalid_grades_raise_errors():
    with pytest.raises(ValueError):
        grade_to_points("Z")
    with pytest.raises(ValueError):
        percent_to_letter(105)


# ----- GPA -----

def test_gpa_is_credit_weighted():
    courses = [
        {"credits": 0.5, "grade": "A+"},   # 12
        {"credits": 1.0, "grade": "B"},    # 8
    ]
    # (12*0.5 + 8*1.0) / 1.5 = 9.33
    assert calculate_gpa(courses) == 9.33


def test_gpa_skips_ungraded_courses():
    courses = [
        {"credits": 0.5, "grade": "A"},
        {"credits": 0.5, "grade": None},
    ]
    assert calculate_gpa(courses) == 11


def test_gpa_with_no_grades_is_none():
    assert calculate_gpa([]) is None


# ----- target GPA -----

def test_points_needed_for_target():
    courses = [
        {"credits": 0.5, "grade": "B"},    # 8
        {"credits": 0.5, "grade": None},
    ]
    # need (10*1.0 - 4) / 0.5 = 12 -> A+
    assert points_needed_for_target(courses, 10) == (12, "A+")


def test_impossible_target():
    courses = [{"credits": 0.5, "grade": "F"}, {"credits": 0.5, "grade": None}]
    points, letter = points_needed_for_target(courses, 11)
    assert letter is None


# ----- prerequisites -----

CATALOG = {
    "CP104": {"name": "Intro", "credits": 0.5, "prereqs": []},
    "CP164": {"name": "DS I", "credits": 0.5, "prereqs": ["CP104"]},
    "CP213": {"name": "OOP", "credits": 0.5, "prereqs": ["CP164"]},
}


def test_prereq_in_progress_is_pending():
    mine = [{"code": "CP104", "status": "in progress", "grade": None, "credits": 0.5}]
    met, missing, pending = check_prereqs("CP164", CATALOG, mine)
    assert pending == ["CP104"] and missing == []


def test_failed_prereq_is_missing():
    mine = [{"code": "CP104", "status": "completed", "grade": "45", "credits": 0.5}]
    met, missing, pending = check_prereqs("CP164", CATALOG, mine)
    assert missing == ["CP104"]


def test_eligible_courses():
    mine = [{"code": "CP104", "status": "completed", "grade": "A", "credits": 0.5}]
    assert eligible_courses(CATALOG, mine) == [("CP164", False)]
