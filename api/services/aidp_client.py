import subprocess
import os
from api.models.job import JobStatus

def submit_gpu_job(job: dict):
    """
    Submits job to AIDP GPU marketplace.
    Job status remains PENDING until worker actually starts execution.
    """

    env = os.environ.copy()
    env["JOB_ID"] = job["id"]
    env["PROMPT"] = job["prompt"]
    env["STEPS"] = str(job["steps"])

    # Simulate AIDP launching GPU worker
    subprocess.Popen(
        ["python", "gpu_worker/worker.py"],
        env=env,
    )
