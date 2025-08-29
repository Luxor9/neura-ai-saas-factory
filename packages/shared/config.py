"""
NEURA AI SaaS Factory - Shared Configuration Management
Provides unified configuration handling across all packages
"""

import os
from typing import Optional, Dict, Any
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class BaseConfig(BaseSettings):
    """Base configuration class with common settings"""
    
    # Environment
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")
    
    # Security
    jwt_secret: str = Field(default="neura-ai-secret-change-in-production", env="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expire_hours: int = Field(default=24, env="JWT_EXPIRE_HOURS")
    
    # Database
    database_url: str = Field(default="sqlite:///./neura_saas.db", env="DATABASE_URL")
    
    # External APIs
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    stripe_secret_key: Optional[str] = Field(default=None, env="STRIPE_SECRET_KEY")
    stripe_publishable_key: Optional[str] = Field(default=None, env="STRIPE_PUBLISHABLE_KEY")
    
    # Paths
    root_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent)
    data_dir: Path = Field(default_factory=lambda: Path("./data"))
    logs_dir: Path = Field(default_factory=lambda: Path("./logs"))
    
    class Config:
        env_file = ".env"
        case_sensitive = False

class APIConfig(BaseConfig):
    """Configuration specific to the API server"""
    
    # Server settings
    host: str = Field(default="0.0.0.0", env="API_HOST")
    port: int = Field(default=8000, env="API_PORT")
    workers: int = Field(default=1, env="API_WORKERS")
    
    # CORS settings
    cors_origins: list = Field(default=["*"], env="CORS_ORIGINS")
    cors_credentials: bool = Field(default=True, env="CORS_CREDENTIALS")
    
    # Rate limiting
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    
    # File upload
    max_file_size: int = Field(default=10 * 1024 * 1024, env="MAX_FILE_SIZE")  # 10MB

class AuditConfig(BaseConfig):
    """Configuration specific to the audit system"""
    
    # Anaconda settings
    anaconda_path: str = Field(default="D:/ANACONDA", env="ANACONDA_PATH")
    
    # Analysis settings
    max_environments: int = Field(default=50, env="MAX_ENVIRONMENTS")
    analysis_timeout: int = Field(default=300, env="ANALYSIS_TIMEOUT")  # 5 minutes
    
    # Output settings
    report_format: str = Field(default="json", env="REPORT_FORMAT")
    output_dir: Path = Field(default_factory=lambda: Path("./audit_reports"))

class SharedConfig(BaseConfig):
    """Shared configuration for all packages"""
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    
    # Monitoring
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=9090, env="METRICS_PORT")
    
    # Feature flags
    enable_voice: bool = Field(default=False, env="ENABLE_VOICE")
    enable_mobile: bool = Field(default=True, env="ENABLE_MOBILE")
    enable_audit: bool = Field(default=True, env="ENABLE_AUDIT")

# Global configuration instances
base_config = BaseConfig()
api_config = APIConfig()
audit_config = AuditConfig()
shared_config = SharedConfig()

def get_config(package_name: str) -> BaseConfig:
    """Get configuration for a specific package"""
    configs = {
        "api": api_config,
        "audit": audit_config,
        "shared": shared_config,
        "base": base_config
    }
    return configs.get(package_name, base_config)

def get_env_vars() -> Dict[str, Any]:
    """Get all environment variables as a dictionary"""
    return {
        key: value for key, value in os.environ.items()
        if key.startswith(('NEURA_', 'API_', 'AUDIT_', 'JWT_', 'STRIPE_', 'OPENAI_'))
    }

def ensure_directories():
    """Ensure required directories exist"""
    for config in [base_config, api_config, audit_config]:
        if hasattr(config, 'data_dir'):
            config.data_dir.mkdir(parents=True, exist_ok=True)
        if hasattr(config, 'logs_dir'):
            config.logs_dir.mkdir(parents=True, exist_ok=True)
        if hasattr(config, 'output_dir'):
            config.output_dir.mkdir(parents=True, exist_ok=True)

# Initialize directories on import
ensure_directories()