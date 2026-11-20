# People Desk Multi-Agent

A standalone employee management app with its own SQLite database and two specialized Gemini agents:

- The **read agent** can search employees, look up an ID, and summarize the team. It has no write tools.
- The **write agent** handles employee creation, partial updates, and deletion. It can search to resolve a target, validates all changes, and requires a separate `DELETE <id>` confirmation before deleting.

## Run

From this directory, create `.env` from `.env.example`, set `GEMINI_API_KEY`, then start the app:

```bash
../.venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8001 --reload
```

Open http://127.0.0.1:8001. The database is created as `employees.db` in this directory on first run. This app's database is separate from the single-agent app.

## Directory features

- Add, edit, search, filter, and remove employees.
- Track contact information, department, role, start date, salary, and status.
- View headcount, active employees, departments, and payroll totals.
- Export the current directory view as CSV.
- Chat requests are routed locally to either the read-only agent or the write agent.
