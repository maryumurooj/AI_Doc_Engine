"""
Application configuration management
"""

from pydantic_settings import BaseSettings
from pydantic import Field, AnyUrl, validator, ConfigDict
from typing import Optional
import logging
import os
from pathlib import Path

class Settings(BaseSettings):
    """Application settings"""
    
    # Database Configuration
    database_url: AnyUrl = "mysql+pymysql://user:password@localhost/financial_db"
    database_pool_size: int = Field(5, env="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(10, env="DATABASE_MAX_OVERFLOW")
    
    # LLM Configuration
    llm_model: str = Field("llama3", env="LLM_MODEL")
    llm_temperature: float = Field(0.3, env="LLM_TEMPERATURE")
    llm_timeout: int = Field(120, env="LLM_TIMEOUT")
    ollama_base_url: str = Field(
        "http://localhost:11434",
        env="OLLAMA_BASE_URL"
    )
    
    # API Configuration
    api_host: str = Field("0.0.0.0", env="API_HOST")
    api_port: int = Field(8000, env="API_PORT")
    api_workers: int = Field(4, env="API_WORKERS")
    api_reload: bool = Field(False, env="API_RELOAD")
    
    # Security
    secret_key: str = Field(..., env="SECRET_KEY")
    api_key: str = Field(..., env="API_KEY")
    
    # Logging
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_format: str = Field(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="forbid"
    )
    
    @validator("database_url")
    def fix_mysql_url(cls, v):
        """Fix MySQL URL for async connections"""
        if "mysql://" in str(v) and "pymysql" not in str(v):
            return str(v).replace("mysql://", "mysql+pymysql://")
        return v
    
    @property
    def database_config(self) -> dict:
        """Get database configuration as dict"""
        return {
            "url": str(self.database_url),
            "pool_size": self.database_pool_size,
            "max_overflow": self.database_max_overflow,
            "echo": False
        }
    
    @property
    def llm_config(self) -> dict:
        """Get LLM configuration as dict"""
        return {
            "model": self.llm_model,
            "temperature": self.llm_temperature,
            "timeout": self.llm_timeout,
            "base_url": self.ollama_base_url
        }
    
    @property
    def api_config(self) -> dict:
        """Get API configuration as dict"""
        return {
            "host": self.api_host,
            "port": self.api_port,
            "workers": self.api_workers,
            "reload": self.api_reload
        }

def setup_logging(settings: Settings):
    """Configure logging"""
    logging.basicConfig(
        level=settings.log_level,
        format=settings.log_format
    )
    # Silence noisy loggers
    for logger_name in ["httpx", "httpcore"]:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

# Initialize settings
try:
    settings = Settings()
    setup_logging(settings)
except Exception as e:
    print(f"Failed to load configuration: {e}")
    raise