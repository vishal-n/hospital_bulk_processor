# Hospital Bulk Processing System

FastAPI service that accepts hospital CSV uploads, creates hospital records using the deployed Hospital Directory API, and activates created batches once all rows succeed.

## Features

- `POST /hospitals/bulk` - Upload and process CSV (`name,address,phone`)
- `GET /hospitals/bulk/{batch_id}/status` - Poll in-memory processing status
- `POST /hospitals/validate-csv` - Validate CSV format and size before processing
- `GET /health` - Basic health endpoint

## Constraints Implemented

- Maximum CSV size: 20 hospitals
- Required columns: `name,address`
- Optional column: `phone`
- UTF-8 CSV expected

## How Processing Works

1. Validate uploaded CSV
2. Generate `batch_id` (UUID)
3. For each row, call `POST https://hospital-directory.onrender.com/hospitals/` with `creation_batch_id`
4. If all rows succeed, call `PATCH /hospitals/batch/{batch_id}/activate`
5. Return full processing summary

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Open Swagger docs:

- <http://127.0.0.1:8000/docs>

## Sample CSV

```csv
name,address,phone
General Hospital,123 Main St,555-1234
City Medical Center,456 Oak Ave,555-6789
```

## Deployment (Render)

1. Push this project to GitHub.
2. Create a new **Web Service** on Render.
3. Use:
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Deploy and access `/docs`.

## Run with Docker

```bash
docker compose up --build
```

## Notes

- Batch status is stored in memory and resets on restart.
- The service acts as an orchestrator around the deployed directory API.
