from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any


class JobStatus(str, Enum):
    PENDING = "PENDING"
    ROUTING_TO_AIDP = "ROUTING_TO_AIDP"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class JobType(str, Enum):
    TEXT_TO_IMAGE = "TEXT_TO_IMAGE"
    LLM_INFERENCE = "LLM_INFERENCE"
    VIDEO_GENERATION = "VIDEO_GENERATION"
    ZK_PROOF = "ZK_PROOF"


class AIDPNodeInfo(BaseModel):
    """AIDP GPU node information"""
    node_id: Optional[str] = None
    wallet: Optional[str] = None
    gpu: Optional[str] = None
    region: Optional[str] = None


class AIDPProof(BaseModel):
    """Proof of execution on AIDP network"""
    aidp_job_id: Optional[str] = None
    node_id: Optional[str] = None
    node_wallet: Optional[str] = None
    node_gpu: Optional[str] = None
    node_region: Optional[str] = None
    proof_signature: Optional[str] = None
    execution_hash: Optional[str] = None
    verified: bool = False
    verification_status: Optional[str] = None
    verification_mode: Optional[str] = None  # "live" or "simulation"
    tx_hash: Optional[str] = None
    on_chain_url: Optional[str] = None
    block_number: Optional[int] = None
    network: Optional[str] = None  # "devnet" or "mainnet"


class AIDPInfo(BaseModel):
    """AIDP network routing information"""
    aidp_job_id: Optional[str] = None
    network: str = "mainnet"
    status: Optional[str] = None
    assigned_node: Optional[AIDPNodeInfo] = None
    routed_at: Optional[str] = None
    cost_aidp: Optional[float] = None
    api_mode: Optional[str] = None  # "live" or "simulation"


class JobCreateRequest(BaseModel):
    type: JobType = JobType.TEXT_TO_IMAGE
    prompt: str
    steps: int = Field(default=30, ge=10, le=50)


class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    output_url: Optional[str] = None
    compute_cost: Optional[float] = None
    error: Optional[str] = None
    created_at: datetime
    # AIDP Integration Fields
    aidp: Optional[AIDPInfo] = None
    proof_of_execution: Optional[AIDPProof] = None

