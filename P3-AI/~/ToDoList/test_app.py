"""Tests for the task list application."""

import pytest

from app import app, count_tasks_by_priority, tasks


@pytest.fixture
def client():
    tasks.clear()
    app.config.update(TESTING=True)
    with app.test_client() as test_client:
        yield test_client
    tasks.clear()


def test_count_empty_tasks():
    assert count_tasks_by_priority([], "High") == 0


def test_count_one_matching_task():
    assert count_tasks_by_priority([{"priority": "High"}], "High") == 1


def test_count_several_matching_tasks():
    tasks = [{"priority": "High"}, {"priority": "Low"}, {"priority": "High"}]
    assert count_tasks_by_priority(tasks, "High") == 2


def test_count_no_matching_tasks():
    assert count_tasks_by_priority([{"priority": "Low"}], "High") == 0


def test_tasks_are_sorted_and_delete_original_row(client):
    later = {"task": "Later task", "priority": "Low", "category": "Personal", "due_date": "2026-12-10"}
    earlier = {"task": "Earlier task", "priority": "High", "category": "Work", "due_date": "2026-11-20"}
    assert client.post("/add", data=later).status_code == 302
    assert client.post("/add", data=earlier).status_code == 302
    page = client.get("/").get_data(as_text=True)
    assert page.index("Earlier task") < page.index("Later task")
    assert client.post("/delete/1").status_code == 302
    assert tasks == [later]


@pytest.mark.parametrize("field,value", [
    ("task", "  "),
    ("priority", "Urgent"),
    ("category", "Other"),
    ("due_date", "2026-02-30"),
])
def test_rejects_invalid_task_fields(client, field, value):
    data = {"task": "A task", "priority": "High", "category": "Work", "due_date": "2026-11-20"}
    data[field] = value
    assert client.post("/add", data=data).status_code == 400
    assert tasks == []


def test_delete_missing_task_returns_404(client):
    assert client.post("/delete/0").status_code == 404