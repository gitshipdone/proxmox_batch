from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Proxmox Configuration
    proxmox_host: str
    proxmox_user: str
    proxmox_password: Optional[str] = None
    proxmox_token_name: Optional[str] = None
    proxmox_token_value: Optional[str] = None
    proxmox_verify_ssl: bool = False

    # Claude API Configuration
    anthropic_api_key: str
    claude_model: str = "claude-sonnet-4-20250514"
    claude_max_tokens: int = 8000

    # Application Configuration
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    database_url: str = "sqlite:///./proxmox_batch.db"
    output_dir: str = "./output"

    # Analysis Configuration
    batch_size: int = 5  # Process this many VMs/LXCs at a time
    enable_terraform: bool = True
    enable_ansible: bool = True
    enable_security_review: bool = True
    enable_optimization: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
