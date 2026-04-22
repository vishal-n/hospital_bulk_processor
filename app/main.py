import time
import uuid
from datetime import datetime, timezone
from typing import List

from fastapi import FastAPI, File, HTTPException, UploadFile, status

from app.client import directory_client
from app.csv_utils import parse_hospitals_csv
from app.models import BatchStatus, BulkProcessResponse, HospitalProcessResult
from app.storage import batch_store

app = FastAPI(
    title="Hospital Bulk Processing API",
    description="Bulk CSV processing service for Hospital Directory API.",
    version="1.0.0",
)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/hospitals/validate-csv")
async def validate_csv(file: UploadFile = File(...)) -> dict:
    rows = await parse_hospitals_csv(file)
    return {
        "valid": True,
        "total_hospitals": len(rows),
        "message": "CSV is valid for bulk processing.",
    }


@app.get("/hospitals/bulk/{batch_id}/status", response_model=BatchStatus)
async def bulk_status(batch_id: str) -> BatchStatus:
    batch = batch_store.get_batch(batch_id)
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch {batch_id} not found.",
        )
    return batch


@app.post("/hospitals/bulk", response_model=BulkProcessResponse)
async def bulk_create_hospitals(file: UploadFile = File(...)) -> BulkProcessResponse:
    started = time.perf_counter()
    hospitals_csv = await parse_hospitals_csv(file)
    batch_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    batch_store.set_batch(
        BatchStatus(
            batch_id=batch_id,
            status="processing",
            total_hospitals=len(hospitals_csv),
            processed_hospitals=0,
            failed_hospitals=0,
            batch_activated=False,
            started_at=now,
        )
    )

    results: List[HospitalProcessResult] = []
    processed_count = 0
    failed_count = 0

    for row in hospitals_csv:
        payload = {
            "name": row.name,
            "address": row.address,
            "phone": row.phone,
            "creation_batch_id": batch_id,
        }
        try:
            created = await directory_client.create_hospital(payload)
            hospital_id = created.get("id")
            results.append(
                HospitalProcessResult(
                    row=row.row,
                    hospital_id=hospital_id,
                    name=row.name,
                    status="created",
                )
            )
            processed_count += 1
        except HTTPException as exc:
            results.append(
                HospitalProcessResult(
                    row=row.row,
                    name=row.name,
                    status="failed",
                    error=str(exc.detail),
                )
            )
            failed_count += 1

        batch_store.update_batch(
            batch_id,
            processed_hospitals=processed_count,
            failed_hospitals=failed_count,
        )

    batch_activated = False
    if failed_count == 0:
        try:
            await directory_client.activate_batch(batch_id)
            batch_activated = True
            for result in results:
                result.status = "created_and_activated"
        except HTTPException as exc:
            failed_count = len(results)
            processed_count = 0
            batch_store.update_batch(
                batch_id,
                processed_hospitals=processed_count,
                failed_hospitals=failed_count,
                status="failed",
                last_error=f"Activation failed: {exc.detail}",
            )
            elapsed = time.perf_counter() - started
            return BulkProcessResponse(
                batch_id=batch_id,
                total_hospitals=len(hospitals_csv),
                processed_hospitals=processed_count,
                failed_hospitals=failed_count,
                processing_time_seconds=round(elapsed, 3),
                batch_activated=False,
                hospitals=results,
            )

    final_status = (
        "completed"
        if failed_count == 0 and batch_activated
        else ("completed_with_errors" if processed_count > 0 else "failed")
    )
    batch_store.update_batch(
        batch_id,
        status=final_status,
        processed_hospitals=processed_count,
        failed_hospitals=failed_count,
        batch_activated=batch_activated,
        completed_at=datetime.now(timezone.utc),
    )

    elapsed = time.perf_counter() - started
    return BulkProcessResponse(
        batch_id=batch_id,
        total_hospitals=len(hospitals_csv),
        processed_hospitals=processed_count,
        failed_hospitals=failed_count,
        processing_time_seconds=round(elapsed, 3),
        batch_activated=batch_activated,
        hospitals=results,
    )
