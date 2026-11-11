"""
Tests for the website (app.py). They use a temporary file,
so your real my_courses.json is never touched.
"""

import pytest

import storage
from app import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "COURSES_FILE", str(tmp_path / "courses.json"))
    app.config["TESTING"] = True
    return app.test_client()


def test_home_page_loads(client):
    page = client.get("/")
    assert page.status_code == 200
    assert b"Laurier GPA Planner" in page.data


def test_add_course_and_gpa(client):
    client.post("/add", data={"code": "ma123", "term": "fall 2026", "status": "completed", "grade": "82"})
    page = client.get("/").data
    assert b"MA123" in page
    assert b"Linear Algebra" in page   # name filled in from catalog.json
    assert b"10.00" in page            # 82% = A- = 10 points


def test_duplicate_course_rejected(client):
    client.post("/add", data={"code": "CP104", "term": "Fall 2026"})
    client.post("/add", data={"code": "CP104", "term": "Fall 2026"})
    assert len(storage.load_courses()) == 1


def test_bad_grade_rejected(client):
    client.post("/add", data={"code": "CP104", "term": "Fall 2026", "grade": "Z"})
    assert storage.load_courses() == []


def test_set_grade_and_delete(client):
    client.post("/add", data={"code": "CP104", "term": "Fall 2026", "status": "in progress"})
    client.post("/grade/CP104", data={"grade": "A"})
    assert storage.load_courses()[0]["status"] == "completed"
    client.post("/delete/CP104")
    assert storage.load_courses() == []


def test_target_and_prereq_tools(client):
    client.post("/add", data={"code": "CP104", "term": "Fall 2026", "status": "in progress"})
    page = client.get("/?target=10&check=CP164").data
    assert b"at least" in page
    assert b"CP104 in progress" in page


# ----- demo mode (the public website) -----

import app as app_module


@pytest.fixture
def demo_client(tmp_path, monkeypatch):
    monkeypatch.setattr(app_module, "DEMO_MODE", True)
    # If demo mode ever wrote to the file, this would catch it.
    monkeypatch.setattr(storage, "COURSES_FILE", str(tmp_path / "courses.json"))
    app.config["TESTING"] = True
    return app.test_client()


def test_demo_starts_with_sample_courses(demo_client):
    page = demo_client.get("/").data
    assert b"Live demo" in page
    assert b"CP104" in page and b"10.50" in page


def test_demo_visitors_do_not_share_data(demo_client):
    # XX999 isn't in catalog.json, so it can only appear if it's in this visitor's list.
    demo_client.post("/add", data={"code": "XX999", "term": "Fall 2027", "name": "Test Course"})
    assert b"XX999" in demo_client.get("/").data
    other_visitor = app.test_client()
    assert b"XX999" not in other_visitor.get("/").data
    assert storage.load_courses() == []   # nothing written to disk


def test_demo_reset(demo_client):
    # CP104's sample grade (88) shows in its grade box only while it's in the list.
    demo_client.post("/delete/CP104")
    assert b'value="88"' not in demo_client.get("/").data
    demo_client.post("/reset")
    assert b'value="88"' in demo_client.get("/").data
