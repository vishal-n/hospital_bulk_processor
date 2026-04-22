import csv
import io
from typing import List

from fastapi import HTTPException, UploadFile, status

from app.config import settings
from app.models import CSVHospitalRow

REQUIRED_HEADERS = {"name", "address"}
OPTIONAL_HEADERS = {"phone"}


async def parse_hospitals_csv(file: UploadFile) -> List[CSVHospitalRow]:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are supported.",
        )

    raw = await file.read()
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV file is empty.",
        )

    try:
        decoded = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV file must be UTF-8 encoded.",
        ) from exc

    reader = csv.DictReader(io.StringIO(decoded))
    if not reader.fieldnames:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV headers are missing.",
        )

    normalized_headers = {h.strip().lower() for h in reader.fieldnames if h}
    allowed = REQUIRED_HEADERS.union(OPTIONAL_HEADERS)
    unknown = normalized_headers.difference(allowed)
    missing = REQUIRED_HEADERS.difference(normalized_headers)

    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"CSV is missing required headers: {', '.join(sorted(missing))}.",
        )
    if unknown:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"CSV has unsupported headers: {', '.join(sorted(unknown))}.",
        )

    rows: List[CSVHospitalRow] = []
    for idx, raw_row in enumerate(reader, start=1):
        name = (raw_row.get("name") or "").strip()
        address = (raw_row.get("address") or "").strip()
        phone = (raw_row.get("phone") or "").strip() or None

        if not name or not address:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Row {idx} must include non-empty 'name' and 'address'.",
            )

        rows.append(CSVHospitalRow(row=idx, name=name, address=address, phone=phone))

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV must contain at least one hospital row.",
        )

    if len(rows) > settings.max_hospitals_per_csv:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"CSV exceeds maximum size of {settings.max_hospitals_per_csv} hospitals.",
        )

    return rows
