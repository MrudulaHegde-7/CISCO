# Alert Explainer API

This FastAPI service stores monitoring alerts in SQLite and produces deterministic explanations based on each alert's fields. It does not call an AI model or any external service.

## Setup and run

From the workspace root on Linux, use the existing virtual environment:

```bash
source .venv/bin/activate
python -m pip install -r College_Management2/alert_explainer_api/requirements.txt
cd College_Management2/alert_explainer_api
uvicorn main:app --reload
```

Open http://127.0.0.1:8000/docs. Stop the server with Ctrl+C. `alerts.db` is created next to the source files and is not committed.

## Tests

From the workspace root, install test dependencies if necessary and run:

```bash
.venv/bin/python -m pip install pytest httpx
.venv/bin/python -m pytest College_Management2/alert_explainer_api/test_api.py -v
```

Tests use an isolated in-memory database for their requests. See [REVIEW.md](REVIEW.md) for a line-by-line code walkthrough and limitations.