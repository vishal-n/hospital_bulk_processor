from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class CSVHospitalRow(BaseModel):
    row: int
    name: str
    address: str
    phone: Optional[str] = None


class HospitalProcessResult(BaseModel):
    row: int
    name: str
    status: str
    hospital_id: Optional[int] = None
    error: Optional[str] = None


class BulkProcessResponse(BaseModel):
    batch_id: str
    total_hospitals: int
    processed_hospitals: int
    failed_hospitals: int
    processing_time_seconds: float
    batch_activated: bool
    hospitals: List[HospitalProcessResult]


class BatchStatus(BaseModel):
    batch_id: str
    status: str = Field(
        description="One of: processing, completed, failed, completed_with_errors"
    )
    total_hospitals: int
    processed_hospitals: int
    failed_hospitals: int
    batch_activated: bool
    started_at: datetime
    completed_at: Optional[datetime] = None
    last_error: Optional[str] = None
