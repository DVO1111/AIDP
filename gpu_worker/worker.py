import requests
import os
from sd_runner import run_stable_diffusion

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def main():
    """
    This worker simulates an AIDP GPU node pulling a job,
    running it, and sending results back.
    """

    # In real AIDP flow, this payload comes from marketplace job config
    job_payload = {
        "job_id": os.getenv("JOB_ID"),
        "prompt": os.getenv("PROMPT"),
        "steps": int(os.getenv("STEPS", 30)),
    }

    job_id = job_payload["job_id"]

    try:
        output_path = run_stable_diffusion(
            job_payload["prompt"],
            job_payload["steps"],
        )

        # Callback to ACR API
        requests.post(
            f"{API_BASE_URL}/jobs/{job_id}/callback",
            json={
                "status": "COMPLETED",
                "output_url": output_path,
                "compute_cost": 0.15,
            },
            timeout=10,
        )

    except Exception as e:
        requests.post(
            f"{API_BASE_URL}/jobs/{job_id}/callback",
            json={
                "status": "FAILED",
                "error": str(e),
            },
            timeout=10,
        )


if __name__ == "__main__":
    main()
