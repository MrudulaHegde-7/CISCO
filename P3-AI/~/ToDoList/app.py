"""A small Flask task list backed by an in-memory list."""

from datetime import date

from flask import Flask, abort, redirect, render_template, request, url_for


app = Flask(__name__)
tasks = []


def count_tasks_by_priority(tasks, priority):
    """Count tasks whose priority matches the given value.

    Args:
        tasks: Task dictionaries containing a priority.
        priority: Priority to count.

    Returns:
        The number of matching tasks.
    """
    count = 0
    for task in tasks:
        if task["priority"] == priority:
            count += 1
    return count


@app.get("/")
def index():
    """Render tasks in ascending due-date order.

    Returns:
        The rendered task list page.
    """
    ordered_tasks = sorted(enumerate(tasks), key=lambda item: item[1]["due_date"])
    return render_template("index.html", tasks=ordered_tasks)


@app.post("/add")
def add_task():
    """Validate and add a task, then return to the task list.

    Returns:
        A redirect to the task list.
    """
    task = request.form.get("task", "").strip()
    priority = request.form.get("priority", "")
    category = request.form.get("category", "")
    due_date = request.form.get("due_date", "")
    if not task or priority not in {"High", "Medium", "Low"} or category not in {"Work", "Personal", "Health"}:
        abort(400, description="All task fields are required and must be valid.")
    try:
        if date.fromisoformat(due_date).isoformat() != due_date:
            raise ValueError
    except ValueError:
        abort(400, description="Enter a valid due date.")
    tasks.append({"task": task, "priority": priority, "category": category, "due_date": due_date})
    return redirect(url_for("index"))


@app.post("/delete/<int:task_index>")
def delete_task(task_index):
    """Delete a task by its position in the original list.

    Args:
        task_index: Index of the task to delete.

    Returns:
        A redirect to the task list.
    """
    if task_index >= len(tasks):
        abort(404)
    tasks.pop(task_index)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run()