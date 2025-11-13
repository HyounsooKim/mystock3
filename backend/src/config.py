"""
Application configuration using Pydantic settings.
Loads configuration from environment variables with MYSTOCK3_ prefix.
"""

from typing import List
from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_prefix="MYSTOCK3_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # Application
    app_name: str = Field(default="MyStock", alias="MYSTOCK3_APP_NAME")
    app_env: str = Field(default="development", alias="MYSTOCK3_APP_ENV")
    log_level: str = Field(default="INFO", alias="MYSTOCK3_LOG_LEVEL")
    
    # API
    api_v1_prefix: str = Field(default="/api/v1", alias="MYSTOCK3_API_V1_PREFIX")
    backend_cors_origins: List[str] = Field(
        default=['http://localhost:5173', 'http://127.0.0.1:5173'],
        alias="MYSTOCK3_BACKEND_CORS_ORIGINS"
    )
    
    # Security
    secret_key: str = Field(..., alias="MYSTOCK3_SECRET_KEY")
    algorithm: str = Field(default="HS256", alias="MYSTOCK3_ALGORITHM")
    access_token_expire_days: int = Field(default=7, alias="MYSTOCK3_ACCESS_TOKEN_EXPIRE_DAYS")
    
    # Database
    cosmos_endpoint: str = Field(..., alias="MYSTOCK3_COSMOS_ENDPOINT")
    cosmos_key: str = Field(..., alias="MYSTOCK3_COSMOS_KEY")
    cosmos_database_name: str = Field(default="mystockdb", alias="MYSTOCK3_COSMOS_DATABASE_NAME")
    
    # External API
    alpha_vantage_api_key: str = Field(..., alias="MYSTOCK3_ALPHA_VANTAGE_API_KEY")
    stock_cache_ttl_seconds: int = Field(default=60, alias="MYSTOCK3_STOCK_CACHE_TTL_SECONDS")
    
    # Azure (optional for local dev)
    azure_tenant_id: str = Field(default="", alias="MYSTOCK3_AZURE_TENANT_ID")
    azure_subscription_id: str = Field(default="", alias="MYSTOCK3_AZURE_SUBSCRIPTION_ID")
    
    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from JSON string or list."""
        import json
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                # Single origin as string
                return [v]
        elif isinstance(v, list):
            return v
        return [str(v)]
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app_env.lower() == "development"


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get global settings instance (dependency injection pattern).
    
    Returns:
        Global Settings instance
    """
    return settings
