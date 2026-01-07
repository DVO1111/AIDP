from enum import Enum
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class JobStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class JobType(str, Enum):
    TEXT_TO_IMAGE = "TEXT_TO_IMAGE"


class JobCreateRequest(BaseModel):
    type: JobType
    prompt: str
    steps: int = 30


class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    output_url: Optional[str] = None
    compute_cost: Optional[float] = None
    created_at: datetime
