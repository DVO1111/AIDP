import subprocess
import os
from api.models.job import JobStatus
from api.services.aidp_integration import (
    submit_to_aidp_network,
    create_execution_proof,
    AIDPJobContext,
)


def submit_gpu_job(job: dict) -> dict:
    """
    Submits job to AIDP GPU marketplace.
    
    Flow:
    1. Route job through AIDP network (node selection, cost calculation)
    2. Store AIDP routing data in job
    3. Launch GPU worker for execution
    4. Job status remains PENDING until worker actually starts execution.
    
    Returns:
        dict: AIDP routing information
    """
    # Step 1: Submit to AIDP network for routing
    aidp_data = submit_to_aidp_network(job)
    
    # Step 2: Store AIDP data in job for later retrieval
    job["aidp_data"] = aidp_data
    
    # Step 3: Set up environment for GPU worker
    env = os.environ.copy()
    env["JOB_ID"] = job["id"]
    env["AIDP_JOB_ID"] = aidp_data["aidp_job_id"]
    env["PROMPT"] = job["prompt"]
    env["STEPS"] = str(job["steps"])
    env["AIDP_NODE_ID"] = aidp_data["assigned_node"]["node_id"]
    env["AIDP_NODE_WALLET"] = aidp_data["assigned_node"]["wallet"]

    # Step 4: AIDP network dispatches to GPU worker
    subprocess.Popen(
        ["python", "gpu_worker/worker.py"],
        env=env,
    )
    
    return aidp_data


def complete_aidp_job(job: dict, output_url: str, execution_time: float) -> dict:
    """
    Called when GPU worker completes execution.
    Generates proof of execution and records on AIDP network.
    
    Args:
        job: The job dictionary with aidp_data
        output_url: URL to the generated output
        execution_time: Time taken for execution in seconds
        
    Returns:
        dict: Proof of execution data
    """
    aidp_data = job.get("aidp_data", {})
    
    # Generate cryptographic proof of execution
    proof = create_execution_proof(
        job_id=job["id"],
        aidp_data=aidp_data,
        output_url=output_url,
        execution_time=execution_time,
    )
    
    # Store proof in job
    job["proof_of_execution"] = proof
    
    return proof
