# ACR Quick Start Guide

Get the AIDP Agent Compute Router running in 5 minutes.

---

## 1. Setup (2 minutes)

### Clone & Install
```bash
git clone https://github.com/your-org/aidp-agent-compute-router.git
cd aidp-agent-compute-router
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Configure
```bash
cp .env.example .env
# Edit .env and add your AIDP_API_KEY if you have one
# (demo mode works without it)
```

---

## 2. Start API (1 minute)

```bash
uvicorn api.main:app --reload
```

You'll see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

Visit http://localhost:8000/docs for interactive API explorer.

---

## 3. Test (2 minutes)

### Option A: Use the Web Demo
Open `Frontend/index.html` in your browser:
- Enter a prompt: "A sunset over a cyberpunk city"
- Click "Generate Image on AIDP GPU"
- Watch job status update in real-time
- See generated image and metrics

### Option B: Use the Test Script

**Windows:**
```powershell
powershell -ExecutionPolicy Bypass -File scripts/submit_test_job.ps1
```

**Linux/macOS:**
```bash
bash scripts/submit_test_job.sh
```

### Option C: Use cURL

Submit job:
```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "type": "TEXT_TO_IMAGE",
    "prompt": "A cyberpunk city at sunset",
    "steps": 30
  }'
```

Response:
```json
{
  "job_id": "acr_a1b2c3d4e5",
  "status": "PENDING",
  "created_at": "2025-01-08T12:34:56.789Z"
}
```

Check status:
```bash
curl http://localhost:8000/jobs/acr_a1b2c3d4e5
```

Once complete, you'll see:
```json
{
  "job_id": "acr_a1b2c3d4e5",
  "status": "COMPLETED",
  "output_url": "outputs/abc123.png",
  "compute_cost": 0.15,
  "created_at": "2025-01-08T12:34:56.789Z"
}
```

---

## 4. What's Happening?

```
Your Request
    ↓
API validates & creates job
    ↓
GPU worker subprocess starts
    ↓
Stable Diffusion runs on GPU (or CPU)
    ↓
Image saved to outputs/
    ↓
Worker sends callback to API
    ↓
API updates job status
    ↓
You get result!
```

---

## 5. Next Steps

- 🔗 **Link to AIDP**: Update `api/services/aidp_client.py` with real AIDP API credentials
- 📊 **Monitor Jobs**: Check `api/services/job_manager.py` to add persistence (SQLite/PostgreSQL)
- 🎯 **Add More Workloads**: Duplicate the TEXT_TO_IMAGE pattern for LLM, video, rendering
- 🐳 **Containerize**: Add Dockerfile for easy deployment
- ☁️ **Deploy**: Push to AWS, GCP, or AIDP marketplace

---

## 6. API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/jobs` | Submit new job |
| GET | `/jobs/{job_id}` | Get job status |
| POST | `/jobs/{job_id}/callback` | Worker posts result |
| GET | `/docs` | Interactive API docs |

---

## 7. Troubleshooting

### "No CUDA device found"
- Falls back to CPU (slower)
- Expected on non-GPU machines
- Set `GPU_DEVICE=cpu` in `.env`

### "Port 8000 already in use"
```bash
uvicorn api.main:app --reload --port 8001
```

### "Module not found" error
```bash
pip install -r requirements.txt
```

### Worker callback fails
- Make sure API is running: `uvicorn api.main:app --reload`
- Check `API_BASE_URL` in `.env`: should be `http://localhost:8000`

---

## 8. Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                  Your Application / Agent               │
└────────────┬────────────────────────────────────────────┘
             │ POST /jobs
             │ {"prompt": "...", "steps": 30}
             ↓
┌─────────────────────────────────────────────────────────┐
│         ACR API (FastAPI) - Port 8000                   │
│  - Validate request                                      │
│  - Create job (PENDING)                                  │
│  - Start GPU worker subprocess                           │
│  - Handle callbacks                                      │
│  - Track job state                                       │
└────────────┬────────────────────────────────────────────┘
             │ spawn
             ↓
┌─────────────────────────────────────────────────────────┐
│           GPU Worker (subprocess)                        │
│  - Load Stable Diffusion model                           │
│  - Generate image on GPU/CPU                             │
│  - Save output to outputs/                               │
│  - POST callback: /jobs/{id}/callback                    │
└──────────────────────────────────────────────────────────┘
```

---

## 9. Performance Tips

- **GPU**: First run downloads ~2GB model; subsequent runs are instant
- **Memory**: Stable Diffusion needs ~6GB VRAM; CPU fallback slower
- **Parallelism**: Currently sequential; next: async queue (Redis/RabbitMQ)
- **Caching**: Model is cached; reuse for batch jobs

---

## 10. Understanding Job Lifecycle

```
1. CREATE JOB
   POST /jobs → API creates job (PENDING) → Returns job_id

2. ROUTE TO WORKER
   API spawns gpu_worker/worker.py subprocess → Job becomes RUNNING

3. EXECUTE
   Worker loads Stable Diffusion → Generates image → Saves to outputs/

4. CALLBACK
   Worker POST /jobs/{id}/callback → API receives result

5. COMPLETED
   Job status → COMPLETED → output_url & compute_cost set

6. RETRIEVE RESULT
   GET /jobs/{id} → You get image URL + metadata
```

---

**Ready? Start with:**
```bash
uvicorn api.main:app --reload
```

Then visit http://localhost:8000/docs 🚀
