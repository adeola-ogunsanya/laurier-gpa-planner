"""
grades.py - Converts grades and calculates GPA using Laurier's 12-point scale.

Source: https://students.wlu.ca/academics/support-and-advising/gpa-calculator/
"""

# Each row is (lowest percentage, letter grade, grade points).
# Ordered from highest to lowest so we can stop at the first match.
GRADE_SCALE = [
    (90, "A+", 12),
    (85, "A", 11),
    (80, "A-", 10),
    (77, "B+", 9),
    (73, "B", 8),
    (70, "B-", 7),
    (67, "C+", 6),
    (63, "C", 5),
    (60, "C-", 4),
    (57, "D+", 3),
    (53, "D", 2),
    (50, "D-", 1),
    (0, "F", 0),
]

PASSING_PERCENT = 50


def percent_to_letter(percent):
    """Return the letter grade for a percentage (e.g. 84 -> 'A-')."""
    if percent < 0 or percent > 100:
        raise ValueError("Percentage must be between 0 and 100.")
    for lowest, letter, points in GRADE_SCALE:
        if percent >= lowest:
            return letter


def letter_to_points(letter):
    """Return the grade points for a letter grade (e.g. 'A-' -> 10)."""
    letter = letter.strip().upper()
    for lowest, scale_letter, points in GRADE_SCALE:
        if letter == scale_letter:
            return points
    raise ValueError(f"'{letter}' is not a valid Laurier letter grade.")


def grade_to_points(grade):
    """
    Accept either a percentage (85 or '85') or a letter ('A') and
    return its grade points.
    """
    if isinstance(grade, (int, float)):
        return letter_to_points(percent_to_letter(grade))
    grade = str(grade).strip()
    try:
        return letter_to_points(percent_to_letter(float(grade)))
    except ValueError:
        # Not a number (or out of range), so try it as a letter.
        return letter_to_points(grade)


def calculate_gpa(courses):
    """
    Calculate a credit-weighted GPA on the 12-point scale.

    courses is a list of dicts, each with a 'credits' value and a 'grade'.
    Courses without a grade yet (in progress or planned) are skipped.
    Returns None if no course has a grade.

    GPA = sum(grade points x credits) / sum(credits)
    """
    total_points = 0
    total_credits = 0
    for course in courses:
        if course.get("grade") is None:
            continue
        total_points += grade_to_points(course["grade"]) * course["credits"]
        total_credits += course["credits"]

    if total_credits == 0:
        return None
    return round(total_points / total_credits, 2)


def points_needed_for_target(courses, target_gpa):
    """
    "What-if" calculator: what average do you need in your ungraded
    courses to reach target_gpa overall?

    Returns (points_needed, letter) where letter is the lowest letter
    grade that gets you there, or (points_needed, None) if it's
    impossible (needs more than 12 points).
    Returns None if there are no ungraded courses.
    """
    graded_points = 0
    graded_credits = 0
    ungraded_credits = 0
    for course in courses:
        if course.get("grade") is None:
            ungraded_credits += course["credits"]
        else:
            graded_points += grade_to_points(course["grade"]) * course["credits"]
            graded_credits += course["credits"]

    if ungraded_credits == 0:
        return None

    # target = (graded_points + x * ungraded_credits) / total_credits, solve for x
    total_credits = graded_credits + ungraded_credits
    points_needed = (target_gpa * total_credits - graded_points) / ungraded_credits
    points_needed = max(points_needed, 0)

    if points_needed > 12:
        return (round(points_needed, 2), None)

    # Find the lowest letter whose points reach what's needed.
    for lowest, letter, points in reversed(GRADE_SCALE):
        if points >= points_needed:
            return (round(points_needed, 2), letter)


def is_passing(grade):
    """True if the grade is a D- (50%) or better."""
    return grade_to_points(grade) > 0
