"""
planner.py - Laurier Course & GPA Planner (run this file).

    python planner.py
"""

from grades import calculate_gpa, grade_to_points, percent_to_letter, points_needed_for_target
from prereqs import check_prereqs, eligible_courses
from storage import load_courses, save_courses, load_catalog

STATUSES = ["completed", "in progress", "planned"]
SEASONS = ["Winter", "Spring", "Summer", "Fall"]  # order within a year


# ---------- helpers ----------

def term_sort_key(term):
    """Sort terms in time order, e.g. 'Fall 2026' before 'Winter 2027'."""
    parts = term.split()
    if len(parts) == 2 and parts[0] in SEASONS and parts[1].isdigit():
        return (int(parts[1]), SEASONS.index(parts[0]))
    return (9999, 0)  # unknown formats go last


def ask(prompt, allow_blank=False):
    """input() that won't accept an empty answer unless allowed."""
    while True:
        answer = input(prompt).strip()
        if answer or allow_blank:
            return answer
        print("  Please enter something.")


def ask_grade(prompt):
    """Ask for a grade (percent or letter). Blank means no grade yet."""
    while True:
        answer = input(prompt).strip()
        if answer == "":
            return None
        try:
            grade_to_points(answer)  # just checking it's valid
            return answer.upper()
        except ValueError:
            print("  Enter a percentage (0-100) or a letter like A-, B+.")


def describe_grade(grade):
    """Show a grade nicely, e.g. '84 (A-, 10 pts)'."""
    if grade is None:
        return "-"
    points = grade_to_points(grade)
    try:
        letter = percent_to_letter(float(grade))
        return f"{grade}% ({letter}, {points} pts)"
    except ValueError:
        return f"{grade} ({points} pts)"


def find_course(courses, code):
    for course in courses:
        if course["code"] == code:
            return course
    return None


def format_gpa(gpa):
    return "n/a" if gpa is None else f"{gpa:.2f} / 12"


# ---------- menu actions ----------

def view_courses(courses):
    if not courses:
        print("\nNo courses yet. Choose 'Add a course' to start.")
        return
    terms = sorted({c["term"] for c in courses}, key=term_sort_key)
    for term in terms:
        term_courses = [c for c in courses if c["term"] == term]
        print(f"\n=== {term}  (term GPA: {format_gpa(calculate_gpa(term_courses))}) ===")
        for c in term_courses:
            print(f"  {c['code']:<7} {c['name'][:34]:<34} {c['credits']:<5} "
                  f"{c['status']:<12} {describe_grade(c.get('grade'))}")


def add_course(courses, catalog):
    code = ask("Course code (e.g. CP164): ").upper().replace(" ", "")
    if find_course(courses, code):
        print(f"  {code} is already in your list. Use 'Enter a grade' to update it.")
        return

    info = catalog.get(code, {})
    name = info.get("name") or ask("Course name: ")
    credits = info.get("credits", 0.5)
    term = ask("Term (e.g. Winter 2027): ").title()

    print("Status: 1) completed  2) in progress  3) planned")
    choice = ask("Choose 1-3: ")
    status = STATUSES[int(choice) - 1] if choice in ("1", "2", "3") else "planned"

    grade = None
    if status == "completed":
        grade = ask_grade("Final grade (percent or letter): ")

    courses.append({"code": code, "name": name, "credits": credits,
                    "term": term, "status": status, "grade": grade})
    save_courses(courses)
    print(f"  Added {code}.")

    # Warn right away if prerequisites aren't covered.
    met, missing, pending = check_prereqs(code, catalog, courses)
    if missing:
        print(f"  Heads up: you haven't taken {', '.join(missing)} yet (prerequisite).")


def enter_grade(courses):
    code = ask("Course code: ").upper().replace(" ", "")
    course = find_course(courses, code)
    if not course:
        print(f"  {code} isn't in your list.")
        return
    grade = ask_grade("Final grade (percent or letter, blank to clear): ")
    course["grade"] = grade
    course["status"] = "completed" if grade is not None else "in progress"
    save_courses(courses)
    print(f"  {code}: {describe_grade(grade)}")


def remove_course(courses):
    code = ask("Course code to remove: ").upper().replace(" ", "")
    course = find_course(courses, code)
    if not course:
        print(f"  {code} isn't in your list.")
        return
    courses.remove(course)
    save_courses(courses)
    print(f"  Removed {code}.")


def show_gpa(courses):
    print(f"\nCumulative GPA: {format_gpa(calculate_gpa(courses))}")
    graded = [c for c in courses if c.get("grade") is not None]
    print(f"Credits graded: {sum(c['credits'] for c in graded)}")


def what_if(courses):
    current = [c for c in courses if c["status"] != "planned"]
    try:
        target = float(ask("Target GPA (out of 12): "))
    except ValueError:
        print("  Enter a number like 9.5")
        return
    result = points_needed_for_target(current, target)
    if result is None:
        print("  You have no in-progress courses to calculate for.")
        return
    points, letter = result
    if letter is None:
        print(f"  Not reachable this term: you'd need {points} points on average (max is 12).")
    else:
        print(f"  You need about {points} points on average in your in-progress courses,")
        print(f"  which means a grade of at least {letter} in each of them.")


def prereq_check(courses, catalog):
    code = ask("Course you want to take: ").upper().replace(" ", "")
    if code not in catalog:
        print(f"  {code} isn't in catalog.json yet. Add it with its prerequisites.")
        return
    met, missing, pending = check_prereqs(code, catalog, courses)
    if not (met or missing or pending):
        print(f"  {code} has no prerequisites listed.")
        return
    if met:
        print(f"  Done:        {', '.join(met)}")
    if pending:
        print(f"  In progress: {', '.join(pending)}")
    if missing:
        print(f"  Still need:  {', '.join(missing)}")
    elif pending:
        print(f"  You can take {code} once you pass {', '.join(pending)}.")
    else:
        print(f"  You can take {code}.")


def next_courses(courses, catalog):
    options = eligible_courses(catalog, courses)
    if not options:
        print("\nNothing new is available from catalog.json right now.")
        return
    print("\nCourses you can take next:")
    for code, is_pending in options:
        note = "  (once your current courses are passed)" if is_pending else ""
        print(f"  {code:<7} {catalog[code]['name']}{note}")


# ---------- main loop ----------

MENU = """
------ Laurier Course & GPA Planner ------
 1) View my courses
 2) Add a course
 3) Enter a grade
 4) Remove a course
 5) Show my GPA
 6) What grade do I need? (target GPA)
 7) Check prerequisites for a course
 8) What can I take next?
 0) Quit"""


def main():
    courses = load_courses()
    catalog = load_catalog()
    while True:
        print(MENU)
        choice = input("Choose an option: ").strip()
        if choice == "1":
            view_courses(courses)
        elif choice == "2":
            add_course(courses, catalog)
        elif choice == "3":
            enter_grade(courses)
        elif choice == "4":
            remove_course(courses)
        elif choice == "5":
            show_gpa(courses)
        elif choice == "6":
            what_if(courses)
        elif choice == "7":
            prereq_check(courses, catalog)
        elif choice == "8":
            next_courses(courses, catalog)
        elif choice == "0":
            print("Saved. Bye!")
            break
        else:
            print("  Pick a number from the menu.")


if __name__ == "__main__":
    main()
