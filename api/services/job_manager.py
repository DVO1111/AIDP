import uuid
from datetime import datetime
from typing import Dict

from api.models.job import JobStatus, JobCreateRequest


# Temporary in-memory store (acceptable for hackathon)
JOBS: Dict[str, dict] = {}


def create_job(payload: JobCreateRequest) -> dict:
    job_id = f"acr_{uuid.uuid4().hex[:10]}"

    job = {
        "id": job_id,
        "type": payload.type,
        "prompt": payload.prompt,
        "steps": payload.steps,
        "status": JobStatus.PENDING,
        "created_at": datetime.utcnow(),
        "output_url": None,
        "compute_cost": None,
        "error": None,
    }

    JOBS[job_id] = job
    return job


def get_job(job_id: str) -> dict:
    return JOBS.get(job_id)


def update_job(job: dict, data: dict):
    """Update job status from GPU worker callback."""
    job["status"] = JobStatus(data["status"])
    job["completed_at"] = datetime.utcnow()
    job["output_url"] = data.get("output_url")
    job["compute_cost"] = data.get("compute_cost")
    if "error" in data:
        job["error"] = data["error"]
    