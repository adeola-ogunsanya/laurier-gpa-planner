"""
prereqs.py - Checks which prerequisites you've met and which courses
you're eligible to take next.

A prerequisite counts as met if you passed it (D- or better).
If you're taking it right now, it counts as "pending".
"""

from grades import is_passing


def course_status(code, my_courses):
    """
    Return 'passed', 'in progress', 'planned', 'failed', or None
    for a course code, based on your course list.
    """
    best = None
    for course in my_courses:
        if course["code"] != code:
            continue
        if course.get("grade") is not None:
            if is_passing(course["grade"]):
                return "passed"  # a pass beats anything else
            best = "failed"
        elif course["status"] == "in progress":
            best = "in progress"
        elif best is None:
            best = "planned"
    return best


def check_prereqs(code, catalog, my_courses):
    """
    Return (met, missing, pending):
      met     - prerequisites you've passed
      missing - prerequisites you haven't passed or started
      pending - prerequisites you're taking right now
    """
    met, missing, pending = [], [], []
    prereqs = catalog.get(code, {}).get("prereqs", [])
    for prereq in prereqs:
        status = course_status(prereq, my_courses)
        if status == "passed":
            met.append(prereq)
        elif status == "in progress":
            pending.append(prereq)
        else:
            missing.append(prereq)
    return met, missing, pending


def eligible_courses(catalog, my_courses):
    """
    List catalog courses you haven't passed or started yet, and whose
    prerequisites are all passed (or in progress).
    Returns a list of (code, is_pending) tuples.
    """
    results = []
    for code in sorted(catalog):
        if course_status(code, my_courses) in ("passed", "in progress"):
            continue
        met, missing, pending = check_prereqs(code, catalog, my_courses)
        if not missing:
            results.append((code, len(pending) > 0))
    return results
