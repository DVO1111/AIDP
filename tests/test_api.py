"""
Test suite for AIDP Agent Compute Router

Run with: pytest tests/

Install test dependencies:
pip install pytest pytest-asyncio httpx
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.services.job_manager import JOBS

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_jobs():
    """Clear jobs before each test"""
    JOBS.clear()
    yield
    JOBS.clear()


class TestJobSubmission:
    """Test job submission endpoints"""

    def test_submit_valid_job(self):
        """Test submitting a valid job"""
        response = client.post(
            "/jobs",
            json={
                "type": "TEXT_TO_IMAGE",
                "prompt": "A test image",
                "steps": 30
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "PENDING"
        assert data["job_id"].startswith("acr_")

    def test_submit_job_missing_prompt(self):
        """Test submitting job without prompt"""
        response = client.post(
            "/jobs",
            json={
                "type": "TEXT_TO_IMAGE",
                "steps": 30
            }
        )
        assert response.status_code == 422  # Validation error

    def test_submit_job_invalid_steps(self):
        """Test submitting job with invalid steps"""
        response = client.post(
            "/jobs",
            json={
                "type": "TEXT_TO_IMAGE",
                "prompt": "Test",
                "steps": 0
            }
        )
        assert response.status_code == 422  # Validation error

    def test_submit_job_default_steps(self):
        """Test that steps default to 30"""
        response = client.post(
            "/jobs",
            json={
                "type": "TEXT_TO_IMAGE",
                "prompt": "A test image"
            }
        )
        assert response.status_code == 200
        data = response.json()
        # Check in job manager
        job = JOBS[data["job_id"]]
        assert job["steps"] == 30


class TestJobStatus:
    """Test job status endpoints"""

    def test_get_nonexistent_job(self):
        """Test getting a job that doesn't exist"""
        response = client.get("/jobs/nonexistent")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_pending_job(self):
        """Test getting a pending job"""
        # Create job
        create_response = client.post(
            "/jobs",
            json={
                "type": "TEXT_TO_IMAGE",
                "prompt": "Test",
                "steps": 30
            }
        )
        job_id = create_response.json()["job_id"]

        # Get job
        get_response = client.get(f"/jobs/{job_id}")
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["job_id"] == job_id
        assert data["status"] == "PENDING"

    def test_get_completed_job(self):
        """Test getting a completed job"""
        # Create job
        create_response = client.post(
            "/jobs",
            json={
                "type": "TEXT_TO_IMAGE",
                "prompt": "Test",
                "steps": 30
            }
        )
        job_id = create_response.json()["job_id"]

        # Simulate completion via callback
        callback_response = client.post(
            f"/jobs/{job_id}/callback",
            json={
                "status": "COMPLETED",
                "output_url": "outputs/test.png",
                "compute_cost": 0.15
            }
        )
        assert callback_response.status_code == 200

        # Get job
        get_response = client.get(f"/jobs/{job_id}")
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["status"] == "COMPLETED"
        assert data["output_url"] == "outputs/test.png"
        assert data["compute_cost"] == 0.15


class TestJobCallback:
    """Test job callback endpoints"""

    def test_callback_completion(self):
        """Test callback with completion"""
        # Create job
        create_response = client.post(
            "/jobs",
            json={
                "type": "TEXT_TO_IMAGE",
                "prompt": "Test",
                "steps": 30
            }
        )
        job_id = create_response.json()["job_id"]

        # Send callback
        callback_response = client.post(
            f"/jobs/{job_id}/callback",
            json={
                "status": "COMPLETED",
                "output_url": "outputs/abc123.png",
                "compute_cost": 0.20
            }
        )
        assert callback_response.status_code == 200
        assert callback_response.json()["status"] == "acknowledged"

        # Verify job was updated
        get_response = client.get(f"/jobs/{job_id}")
        data = get_response.json()
        assert data["status"] == "COMPLETED"
        assert data["output_url"] == "outputs/abc123.png"
        assert data["compute_cost"] == 0.20

    def test_callback_failure(self):
        """Test callback with failure"""
        # Create job
        create_response = client.post(
            "/jobs",
            json={
                "type": "TEXT_TO_IMAGE",
                "prompt": "Test",
                "steps": 30
            }
        )
        job_id = create_response.json()["job_id"]

        # Send failure callback
        callback_response = client.post(
            f"/jobs/{job_id}/callback",
            json={
                "status": "FAILED",
                "error": "Out of memory on GPU"
            }
        )
        assert callback_response.status_code == 200

        # Verify job was updated
        get_response = client.get(f"/jobs/{job_id}")
        data = get_response.json()
        assert data["status"] == "FAILED"
        assert "error" in data

    def test_callback_nonexistent_job(self):
        """Test callback for nonexistent job"""
        response = client.post(
            "/jobs/nonexistent/callback",
            json={
                "status": "COMPLETED",
                "output_url": "outputs/test.png"
            }
        )
        assert response.status_code == 404


class TestAPIDocumentation:
    """Test API documentation endpoints"""

    def test_openapi_docs(self):
        """Test that OpenAPI docs are available"""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "swagger" in response.text.lower()

    def test_redoc_docs(self):
        """Test that ReDoc docs are available"""
        response = client.get("/redoc")
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
