# People Desk

A local employee management app with an SQLite database, employee directory, CSV export, and one read-only Gemini assistant.

## Run

From this directory, start the app with the workspace virtual environment:

```bash
../.venv/bin/python -m uvicorn main:app --reload
```

Open http://127.0.0.1:8000. The database is created as `employees.db` in this directory on first run.

The directory works without an AI key. To enable the People assistant, create a `.env` file in this directory using `.env.example` and set `GEMINI_API_KEY`. Restart the app after changing environment settings.

## Features

- Add, edit, search, filter, and remove employees.
- Track contact details, department, role, start date, salary, and status.
- View headcount, active employees, departments, and annual payroll totals.
- Export the current directory view as CSV.
- Ask the read-only assistant questions about employee records and team totals.
- SQLite data persists locally between restarts.

The assistant can search records and calculate database summaries, but it cannot change employee data. Use the directory controls for record changes.
