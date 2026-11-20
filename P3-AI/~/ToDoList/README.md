# Worklist

A Flask to-do list for adding and deleting tasks with a priority, category, and due date. Tasks are displayed in due-date order and stored in memory, so they are lost when the server restarts. This is a local demonstration, not a persistent or multi-user task manager.

## Setup

Python 3.10 or later is required. From the `ToDoList` folder on Linux, activate the existing workspace environment and install the dependencies:

```bash
source ../.venv/bin/activate
python -m pip install flask pytest
```

If the workspace environment does not exist, create it from `ToDoList` with `python3 -m venv ../.venv` before activating it.

## Run

```bash
python app.py
```

Open http://127.0.0.1:5000 and press Ctrl+C in the terminal to stop the server.

## Test

```bash
python -m pytest test_app.py -v
```