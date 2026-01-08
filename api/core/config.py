"""
Configuration management for AIDP Agent Compute Router
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Server
    api_base_url: str = "http://localhost:8000"
    api_port: int = 8000
    api_host: str = "0.0.0.0"

    # AIDP Integration
    aidp_api_key: str = ""
    aidp_marketplace_url: str = "https://marketplace.aidp.store"
    aidp_network: str = "solana_mainnet"

    # GPU Configuration
    gpu_device: str = "cuda"
    use_half_precision: bool = True
    model_id: str = "runwayml/stable-diffusion-v1-5"

    # Job Execution
    default_steps: int = 30
    max_steps: int = 50
    job_timeout_seconds: int = 300
    compute_cost_per_image: float = 0.15

    # Storage
    output_dir: str = "./outputs"
    enable_s3_storage: bool = False

    # Logging
    log_level: str = "INFO"
    environment: str = "development"
    debug: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
