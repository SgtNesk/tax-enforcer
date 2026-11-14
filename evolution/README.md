# Tax Enforcer Evolution Lab

Laboratory prototype for reconciling claims and reviewing evidence. Use synthetic inputs for audit, lifecycle simulation, PDF drafts and camera intake. Case storage is optional. PDF drafts carry a non-binding label.

## Run locally

From this directory, use Python 3.12.

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-test.txt
python -m pytest -q
python -m src.citizen_audit.cli example_case.json
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The interface is at http://127.0.0.1:8000/ and the health endpoint at http://127.0.0.1:8000/health.

The case and draft endpoints require a local `OPERATOR_TOKEN` of at least 32 characters. The case endpoints also require `CASE_DB_PATH` to point to a private writable location. SPID remains disabled until accredited configuration is supplied. Keep this lab local.
