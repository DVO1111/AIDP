# Deployment Guide

How to deploy ACR to production and integrate with real AIDP.

---

## Phase 1: Local Development (You Are Here ✓)

**Status**: ✅ Complete

- FastAPI running locally
- Stable Diffusion inference on GPU
- In-memory job store
- Frontend demo

**Next**: Phase 2

---

## Phase 2: Production Deployment (2-3 days)

### 2.1 Docker Containerization

Create `Dockerfile`:

```dockerfile
FROM nvidia/cuda:12.0-runtime-ubuntu22.04

WORKDIR /app

# Install Python
RUN apt-get update && apt-get install -y python3.10 python3-pip
RUN pip install --upgrade pip

# Copy requirements
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy code
COPY api/ ./api/
COPY gpu_worker/ ./gpu_worker/
COPY Frontend/ ./Frontend/

# Expose port
EXPOSE 8000

# Run API
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build:
```bash
docker build -t aidp-acr:latest .
```

Run:
```bash
docker run --gpus all -p 8000:8000 -e AIDP_API_KEY=$AIDP_API_KEY aidp-acr:latest
```

### 2.2 Database Persistence

Replace in-memory store with PostgreSQL:

```python
# api/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://user:password@localhost/aidp_acr"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)
```

Update `job_manager.py` to use SQLAlchemy ORM.

### 2.3 Job Queue (Redis)

Add Redis for async job handling:

```python
# api/queue.py
import redis
from rq import Queue

redis_conn = redis.Redis()
job_queue = Queue(connection=redis_conn)

# Enqueue job
def submit_gpu_job(job):
    job_queue.enqueue('gpu_worker.worker.run_job', job)
```

### 2.4 Environment Configuration

`.env.production`:
```
ENVIRONMENT=production
AIDP_API_KEY=your_real_key
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
LOG_LEVEL=INFO
DEBUG=false
```

### 2.5 Testing

Run tests before deploy:
```bash
pytest tests/ -v
```

---

## Phase 3: AIDP Integration (1 week)

### 3.1 Register with AIDP Marketplace

1. Create account: https://marketplace.aidp.store
2. Create project entry with:
   - Project name
   - Description
   - GitHub repo link
   - Demo video
   - API documentation

### 3.2 Implement Real AIDP Client

Update `api/services/aidp_client.py`:

```python
# api/services/aidp_client.py
import httpx
from api.core.config import get_settings

settings = get_settings()
AIDP_API_KEY = settings.aidp_api_key
AIDP_ENDPOINT = settings.aidp_marketplace_url

async def submit_gpu_job(job: dict):
    """Submit job to real AIDP marketplace"""
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AIDP_ENDPOINT}/jobs",
            headers={"Authorization": f"Bearer {AIDP_API_KEY}"},
            json={
                "job_id": job["id"],
                "type": "TEXT_TO_IMAGE",
                "prompt": job["prompt"],
                "steps": job["steps"],
                "callback_url": f"{settings.api_base_url}/jobs/{job['id']}/callback"
            }
        )
        
        if response.status_code != 202:
            raise Exception(f"AIDP error: {response.text}")
        
        data = response.json()
        job["aidp_job_id"] = data["job_id"]
        job["gpu_provider"] = data["provider"]
        job["aidp_cost_estimate"] = data["estimated_cost"]
```

### 3.3 Handle Staking & Proofs

AIDP uses staking for GPU provider reliability. Update job tracking:

```python
# api/models/job.py
class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    aidp_job_id: str  # NEW
    gpu_provider: str  # NEW
    provider_stake: float  # NEW: staked AIDP tokens
    execution_proof: str  # NEW: verifiable execution hash
    compute_cost: float
```

### 3.4 Cost Attribution

Track actual costs from AIDP:

```python
# Track per job
job["aidp_execution_time"] = 45  # seconds
job["aidp_gpu_memory"] = 6500    # MB
job["aidp_compute_cost"] = 0.15  # USDC or AIDP

# Aggregate for billing
monthly_spend = sum(job["aidp_compute_cost"] 
                   for job in completed_jobs 
                   if job["month"] == current_month)
```

---

## Phase 4: Scale & Optimization (2-4 weeks)

### 4.1 Add More Workload Types

Duplicate pattern for:

**LLM Inference**:
```python
# gpu_worker/llm_runner.py
from transformers import AutoModelForCausalLM, AutoTokenizer

def run_llm_inference(prompt: str, model_id: str = "mistralai/Mistral-7B"):
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(model_id)
    inputs = tokenizer(prompt, return_tensors="pt")
    outputs = model.generate(**inputs, max_length=200)
    return tokenizer.decode(outputs[0])
```

**Video Generation**:
```python
# gpu_worker/video_runner.py
from stable_video_diffusion import SVDPipeline

def run_video_generation(prompt: str, num_frames: int = 25):
    pipe = SVDPipeline.from_pretrained("stabilityai/stable-video-diffusion-img2vid")
    video = pipe(prompt, num_frames=num_frames).video
    return save_video(video)
```

**ZK Proof Generation**:
```python
# gpu_worker/zk_runner.py
from circom_py import CircomRunner

def generate_zk_proof(circuit: str, inputs: dict):
    runner = CircomRunner(circuit)
    proof = runner.prove(inputs)
    return proof
```

### 4.2 Performance Optimization

- **Model Caching**: Keep model in VRAM between jobs
- **Batch Processing**: Support multiple jobs per GPU
- **Load Balancing**: Route to available GPU providers
- **Rate Limiting**: Prevent abuse

### 4.3 Monitoring & Analytics

```python
# api/monitoring.py
import prometheus_client as pc

job_counter = pc.Counter('acr_jobs_total', 'Total jobs')
job_duration = pc.Histogram('acr_job_duration_seconds', 'Job duration')
acr_cost = pc.Counter('acr_total_cost_usdc', 'Total cost')

# Use in job completion:
job_duration.observe(job["execution_time"])
acr_cost.inc(job["compute_cost"])
```

Dashboard: Grafana + Prometheus

---

## Phase 5: Official Marketplace Integration

### Final Checklist

- [ ] Real AIDP API credentials working
- [ ] Cost attribution accurate
- [ ] Execution proofs verifiable
- [ ] Multiple GPU providers available
- [ ] SLA monitoring (uptime, latency)
- [ ] Rate limiting & quotas
- [ ] Production logging
- [ ] Incident response plan

### Publish to AIDP Marketplace

1. Submit to marketplace verification team
2. Get approved as official ACR integration
3. List on AIDP dashboard
4. Marketing launch

---

## Deployment Commands

### Development
```bash
uvicorn api.main:app --reload
```

### Production (Docker)
```bash
docker build -t aidp-acr:latest .
docker run --gpus all -p 8000:8000 --env-file .env.production aidp-acr:latest
```

### Production (Cloud)

**AWS EC2 (GPU)**:
```bash
# Launch g4dn.xlarge instance
# SSH into instance
git clone https://github.com/your-org/aidp-agent-compute-router.git
cd aidp-agent-compute-router
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
nohup uvicorn api.main:app --host 0.0.0.0 --port 8000 > api.log 2>&1 &
```

**Google Cloud Run** (CPU only):
```bash
# For frontend only (no GPU)
gcloud run deploy acr --source . --platform managed --region us-central1
```

**Modal** (Serverless GPU):
```python
# modal_deployment.py
import modal

app = modal.App("aidp-acr")
gpu = modal.gpu.T4()

@app.function(gpu=gpu)
def run_inference(prompt: str):
    from gpu_worker.sd_runner import run_stable_diffusion
    return run_stable_diffusion(prompt)
```

---

## Monitoring Checklist

- [ ] API health endpoint: `GET /health`
- [ ] GPU utilization metrics
- [ ] Job success rate tracking
- [ ] Cost tracking per user
- [ ] Error rate monitoring
- [ ] Latency SLA monitoring
- [ ] Uptime alerts
- [ ] Cost anomaly detection

---

## Security Considerations

1. **API Authentication**: Add Bearer token auth
2. **Rate Limiting**: 100 requests/minute per user
3. **Cost Limits**: Max $10/day per user
4. **Audit Logging**: Log all job submissions
5. **Input Validation**: Prevent prompt injection
6. **Secret Management**: Use AWS Secrets Manager for AIDP keys

---

## Rollback Plan

If issues occur:

```bash
# Rollback to previous image
docker run --gpus all -p 8000:8000 aidp-acr:v1.0.0

# Check logs
docker logs <container_id>

# Notify users
POST /notifications/send "Service downtime 5 minutes"
```

---

## Cost Estimation

| Component | Monthly Cost |
|-----------|-------------|
| AWS G4DN.xlarge | $500 |
| PostgreSQL RDS | $50 |
| Redis | $20 |
| Monitoring (Datadog) | $100 |
| **Total** | **$670** |

Revenue model: Charge 20% markup on GPU costs
- AIDP cost: $0.15 per image
- Your price: $0.18 per image
- Margin: 20%

---

## Success Metrics

Track these KPIs:

- **Usage**: Jobs/day
- **Growth**: MoM usage growth
- **Cost**: AIDP spend vs revenue
- **Quality**: Job success rate (target: >99%)
- **Speed**: Avg job latency
- **User Satisfaction**: NPS score

---

**Next**: Update AIDP integration once keys are available 🚀
