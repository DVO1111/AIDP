from fastapi import APIRouter, HTTPException
from api.models.job import JobCreateRequest, JobResponse
from api.services.job_manager import create_job, get_job
from api.services.aidp_client import submit_gpu_job

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post("/", response_model=JobResponse)
def create_compute_job(payload: JobCreateRequest):
    job = create_job(payload)

    # Route job to AIDP GPU
    submit_gpu_job(job)

    return JobResponse(
        job_id=job["id"],
        status=job["status"],
        output_url=job["output_url"],
        compute_cost=job["compute_cost"],
        created_at=job["created_at"],
    )


@router.get("/{job_id}", response_model=JobResponse)
def get_compute_job(job_id: str):
    job = get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobResponse(
        job_id=job["id"],
        status=job["status"],
        output_url=job["output_url"],
        compute_cost=job["compute_cost"],
        created_at=job["created_at"],
    )
from fastapi import Body

@router.post("/{job_id}/callback")
def gpu_job_callback(job_id: str, payload: dict = Body(...)):
    job = get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    from api.services.job_manager import update_job
    update_job(job, payload)

    return {"status": "acknowledged"}

@router.post("/{job_id}/callback")
def gpu_job_callback(job_id: str, payload: dict):
    job = get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    from api.services.job_manager import complete_job
    complete_job(job, payload)

    return {"status": "acknowledged"}
