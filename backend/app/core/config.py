"""Configuration management using pydantic-settings."""
from __future__ import annotations

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/sprintly_mvp"
    
    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate that database URL is properly formatted."""
        if not v:
            raise ValueError("database_url cannot be empty")
        
        v = v.strip()
        
        # Check if URL starts with postgresql:// or postgresql+psycopg2://
        if not (v.startswith("postgresql://") or v.startswith("postgresql+psycopg2://")):
            # If it looks like a malformed URL (e.g., "sprintly@localhost"), provide helpful error
            if "@" in v and not v.startswith(("postgresql://", "postgresql+psycopg2://", "http://", "https://")):
                raise ValueError(
                    f"❌ Invalid database URL format: '{v}'\n\n"
                    "The database URL must start with 'postgresql://' or 'postgresql+psycopg2://'\n"
                    "Expected format: postgresql://username:password@host:port/database_name\n\n"
                    "Example: postgresql://postgres:postgres@localhost:5432/sprintly_mvp\n\n"
                    "If you're using an environment variable, make sure it's set correctly:\n"
                    "  DATABASE_URL=postgresql://username:password@host:port/database_name"
                )
            # Otherwise, prepend postgresql:// if it's missing (for simple cases)
            if not v.startswith(("postgresql://", "postgresql+psycopg2://")):
                v = f"postgresql://{v}"
        
        return v

    # Neo4j
    neo4j_uri: str = "neo4j://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    neo4j_database: str = "neo4j"

    # OpenAI
    openai_api_key: str = ""

    # App
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "*"

    # Upload settings
    max_upload_size: int = 200 * 1024 * 1024  # 200MB

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()

