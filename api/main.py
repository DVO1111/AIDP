from fastapi import FastAPI
from api.routes import jobs

app = FastAPI(
    title="AIDP Agent Compute Router",
    description="Decentralized GPU execution layer for AI agents",
    version="0.1.0",
)

app.include_router(jobs.router)
