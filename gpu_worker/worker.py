import requests
import os
import time
from sd_runner import run_stable_diffusion

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def main():
    """
    This worker simulates an AIDP GPU node pulling a job,
    running it, and sending results back with proof of execution.
    
    AIDP Network Context:
    - JOB_ID: Internal router job ID
    - AIDP_JOB_ID: AIDP network job ID for proof generation
    - AIDP_NODE_ID: This node's ID in AIDP network
    - AIDP_NODE_WALLET: This node's Solana wallet for payment
    """

    # In real AIDP flow, this payload comes from marketplace job config
    job_payload = {
        "job_id": os.getenv("JOB_ID"),
        "aidp_job_id": os.getenv("AIDP_JOB_ID"),
        "prompt": os.getenv("PROMPT"),
        "steps": int(os.getenv("STEPS", 30)),
        "node_id": os.getenv("AIDP_NODE_ID"),
        "node_wallet": os.getenv("AIDP_NODE_WALLET"),
    }

    job_id = job_payload["job_id"]
    aidp_job_id = job_payload["aidp_job_id"]

    try:
        # Track execution time for proof of execution
        start_time = time.time()
        
        output_path = run_stable_diffusion(
            job_payload["prompt"],
            job_payload["steps"],
        )
        
        execution_time = time.time() - start_time

        # Callback to ACR API with execution metrics for proof generation
        requests.post(
            f"{API_BASE_URL}/jobs/{job_id}/callback",
            json={
                "status": "completed",
                "output_url": output_path,
                "compute_cost": 0.15,
                "execution_time": round(execution_time, 2),
                "aidp_job_id": aidp_job_id,
                "node_id": job_payload["node_id"],
            },
            timeout=10,
        )

    except Exception as e:
        requests.post(
            f"{API_BASE_URL}/jobs/{job_id}/callback",
            json={
                "status": "failed",
                "error": str(e),
            },
            timeout=10,
        )


if __name__ == "__main__":
    main()
