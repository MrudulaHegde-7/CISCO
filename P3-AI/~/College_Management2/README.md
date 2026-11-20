# College Management API

FastAPI service for creating and listing departments and students. Data is saved in `college.db` next to the source files.

## Setup and run

From the workspace root on Linux, reuse the existing virtual environment:

```bash
source .venv/bin/activate
python -m pip install -r College_Management2/requirements.txt
cd College_Management2
uvicorn main:app --reload
```

Open http://127.0.0.1:8000/docs for the interactive API documentation. Press Ctrl+C to stop the server. See [REVIEW.md](REVIEW.md) for a line-by-line walkthrough and limitations.

## Tests

From the workspace root, install the test dependencies if necessary and run:

```bash
.venv/bin/python -m pip install pytest httpx
.venv/bin/python -m pytest College_Management2/test_api.py -v
```

The test uses a separate in-memory database, so it does not change application records.