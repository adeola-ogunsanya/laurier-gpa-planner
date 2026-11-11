"""
app.py - Website version of the Laurier Course & GPA Planner.

Run it with:   python app.py
Then open:     http://127.0.0.1:5000  in your browser.

It reuses the same logic as the command-line version:
  grades.py  -> GPA math
  prereqs.py -> prerequisite checks
  storage.py -> saving to my_courses.json

Two ways of saving courses:
  - Normal mode (on your computer): saved to my_courses.json.
  - Demo mode (the public website, DEMO_MODE=1): each visitor gets their
    own private list stored in their browser session, pre-filled with
    sample courses. Nothing is shared between visitors.
"""

import copy
import os

from flask import Flask, render_template, request, redirect, url_for, flash, session

import storage
from grades import calculate_gpa, grade_to_points, percent_to_letter, points_needed_for_target
from prereqs import check_prereqs, eligible_courses
from planner import term_sort_key, find_course

app = Flask(__name__)
# The secret key signs the browser session. Online it comes from an
# environment variable so it isn't public on GitHub.
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-secret")

STATUSES = ["completed", "in progress", "planned"]
DEMO_MODE = os.environ.get("DEMO_MODE") == "1"
DEMO_MAX_COURSES = 25  # browser sessions are small, so keep the list short

SAMPLE_COURSES = [
    {"code": "CP104", "name": "Introduction to Programming", "credits": 0.5,
     "term": "Fall 2026", "status": "completed", "grade": "88"},
    {"code": "MA123", "name": "Linear Algebra", "credits": 0.5,
     "term": "Fall 2026", "status": "completed", "grade": "82"},
    {"code": "ES110", "name": "Environmental Studies", "credits": 0.5,
     "term": "Fall 2026", "status": "in progress", "grade": None},
    {"code": "GG101", "name": "Geography", "credits": 0.5,
     "term": "Fall 2026", "status": "in progress", "grade": None},
    {"code": "CP164", "name": "Data Structures I", "credits": 0.5,
     "term": "Winter 2027", "status": "planned", "grade": None},
]


def load_courses():
    """Get the course list from the right place for the current mode."""
    if DEMO_MODE:
        if "courses" not in session:
            session["courses"] = copy.deepcopy(SAMPLE_COURSES)
        return session["courses"]
    return storage.load_courses()


def save_courses(courses):
    if DEMO_MODE:
        session["courses"] = courses
    else:
        storage.save_courses(courses)


def load_catalog():
    return storage.load_catalog()


def clean_code(text):
    """'cp 104' -> 'CP104'"""
    return text.upper().replace(" ", "")


def valid_grade(text):
    """Return the grade in upper case if it's valid, None if blank, or raise ValueError."""
    text = text.strip()
    if text == "":
        return None
    grade_to_points(text)  # raises ValueError if invalid
    return text.upper()


def grade_label(grade):
    """'84' -> 'A- · 10 pts'"""
    if grade is None:
        return ""
    points = grade_to_points(grade)
    try:
        letter = percent_to_letter(float(grade))
    except ValueError:
        letter = grade
    return f"{letter} · {points} pts"


# ---------- pages ----------

@app.route("/")
def home():
    courses = load_courses()
    catalog = load_catalog()

    # Group courses by term, in time order, with a GPA for each term.
    terms = []
    for term in sorted({c["term"] for c in courses}, key=term_sort_key):
        term_courses = [c for c in courses if c["term"] == term]
        terms.append({"name": term,
                      "gpa": calculate_gpa(term_courses),
                      "courses": term_courses})

    graded = [c for c in courses if c.get("grade") is not None]

    # Target GPA calculator (runs when the form sends ?target=...)
    target = request.args.get("target", "").strip()
    target_result = None
    if target:
        try:
            current = [c for c in courses if c["status"] != "planned"]
            target_result = points_needed_for_target(current, float(target))
            if target_result is None:
                target_result = "none"
        except ValueError:
            flash("Target GPA must be a number, like 9.5", "error")

    # Prerequisite checker (runs when the form sends ?check=...)
    check = clean_code(request.args.get("check", ""))
    check_result = None
    if check:
        if check in catalog:
            met, missing, pending = check_prereqs(check, catalog, courses)
            check_result = {"code": check, "name": catalog[check]["name"],
                            "met": met, "missing": missing, "pending": pending}
        else:
            flash(f"{check} isn't in catalog.json yet.", "error")

    return render_template(
        "index.html",
        terms=terms,
        gpa=calculate_gpa(courses),
        credits_graded=sum(c["credits"] for c in graded),
        course_count=len(courses),
        catalog=catalog,
        next_courses=eligible_courses(catalog, courses),
        target=target, target_result=target_result,
        check=check, check_result=check_result,
        grade_label=grade_label,
        demo_mode=DEMO_MODE,
    )


# ---------- form actions ----------

@app.route("/add", methods=["POST"])
def add():
    courses = load_courses()
    catalog = load_catalog()

    code = clean_code(request.form.get("code", ""))
    term = request.form.get("term", "").strip().title()
    status = request.form.get("status", "planned")

    if not code or not term:
        flash("Course code and term are both required.", "error")
        return redirect(url_for("home"))
    if find_course(courses, code):
        flash(f"{code} is already in your list.", "error")
        return redirect(url_for("home"))
    if DEMO_MODE and len(courses) >= DEMO_MAX_COURSES:
        flash(f"The demo holds up to {DEMO_MAX_COURSES} courses. Remove one or reset the demo.", "error")
        return redirect(url_for("home"))
    if status not in STATUSES:
        status = "planned"

    try:
        grade = valid_grade(request.form.get("grade", ""))
    except ValueError:
        flash("Grade must be a percentage (0–100) or a letter like A-.", "error")
        return redirect(url_for("home"))
    if grade is not None:
        status = "completed"

    info = catalog.get(code, {})
    name = request.form.get("name", "").strip() or info.get("name") or code
    courses.append({"code": code, "name": name, "credits": info.get("credits", 0.5),
                    "term": term, "status": status, "grade": grade})
    save_courses(courses)
    flash(f"Added {code}.", "ok")

    met, missing, pending = check_prereqs(code, catalog, courses)
    if missing:
        flash(f"Heads up: {code} needs {', '.join(missing)} first.", "warn")
    return redirect(url_for("home"))


@app.route("/grade/<code>", methods=["POST"])
def set_grade(code):
    courses = load_courses()
    course = find_course(courses, code)
    if course:
        try:
            course["grade"] = valid_grade(request.form.get("grade", ""))
            course["status"] = "completed" if course["grade"] is not None else "in progress"
            save_courses(courses)
        except ValueError:
            flash("Grade must be a percentage (0–100) or a letter like A-.", "error")
    return redirect(url_for("home"))


@app.route("/delete/<code>", methods=["POST"])
def delete(code):
    courses = load_courses()
    course = find_course(courses, code)
    if course:
        courses.remove(course)
        save_courses(courses)
        flash(f"Removed {code}.", "ok")
    return redirect(url_for("home"))


@app.route("/reset", methods=["POST"])
def reset():
    """Demo mode only: put the sample courses back."""
    if DEMO_MODE:
        session["courses"] = copy.deepcopy(SAMPLE_COURSES)
        flash("Demo reset to the sample courses.", "ok")
    return redirect(url_for("home"))


if __name__ == "__main__":
    print("Open http://127.0.0.1:5000 in your browser. Press Ctrl+C here to stop.")
    app.run(debug=True)
