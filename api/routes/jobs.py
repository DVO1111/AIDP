from fastapi import APIRouter, HTTPException, Body
from api.models.job import (
    JobCreateRequest, 
    JobResponse, 
    AIDPInfo, 
    AIDPProof,
    AIDPNodeInfo,
    JobStatus,
)
from api.services.job_manager import create_job, get_job, update_job
from api.services.aidp_client import submit_gpu_job, complete_aidp_job

router = APIRouter(prefix="/jobs", tags=["Jobs"])


def build_aidp_info(job: dict) -> AIDPInfo | None:
    """Build AIDPInfo model from job's aidp_data."""
    aidp_data = job.get("aidp_data")
    if not aidp_data:
        return None
    
    return AIDPInfo(
        aidp_job_id=aidp_data["aidp_job_id"],
        network=aidp_data["network"],
        status=aidp_data["status"],
        assigned_node=AIDPNodeInfo(**aidp_data["assigned_node"]),
        routed_at=aidp_data["routed_at"],
        cost_aidp=aidp_data["cost_aidp"],
    )


def build_proof(job: dict) -> AIDPProof | None:
    """Build AIDPProof model from job's proof_of_execution."""
    proof_data = job.get("proof_of_execution")
    if not proof_data:
        return None
    
    return AIDPProof(
        aidp_job_id=proof_data["aidp_job_id"],
        proof_signature=proof_data["proof_signature"],
        execution_hash=proof_data["execution_hash"],
        verified=proof_data["verified"],
        on_chain_url=proof_data.get("on_chain_url"),
        tx_hash=proof_data.get("tx_hash"),
        block_number=proof_data.get("block_number"),
    )


@router.post("/", response_model=JobResponse)
def create_compute_job(payload: JobCreateRequest):
    job = create_job(payload)

    # Route job through AIDP GPU network
    aidp_data = submit_gpu_job(job)

    return JobResponse(
        job_id=job["id"],
        status=job["status"],
        output_url=job["output_url"],
        compute_cost=job["compute_cost"],
        error=job.get("error"),
        created_at=job["created_at"],
        aidp=build_aidp_info(job),
        proof_of_execution=None,  # Proof generated on completion
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
        error=job.get("error"),
        created_at=job["created_at"],
        aidp=build_aidp_info(job),
        proof_of_execution=build_proof(job),
    )


@router.post("/{job_id}/callback")
def gpu_job_callback(job_id: str, payload: dict = Body(...)):
    job = get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Update job with callback data
    update_job(job, payload)
    
    # If job completed successfully, generate proof of execution
    if payload.get("status") == "completed" and payload.get("output_url"):
        execution_time = payload.get("execution_time", 0.0)
        proof = complete_aidp_job(job, payload["output_url"], execution_time)
        return {
            "status": "acknowledged",
            "proof_generated": True,
            "aidp_job_id": proof.get("aidp_job_id"),
        }

    return {"status": "acknowledged"}
