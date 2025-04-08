from enum import Enum
from functools import lru_cache
from typing import Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    """Environment env vars supported by DatabaseMCP."""

    LOCAL = "local"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """QueryMCP settings"""

    # Configure environment variables loading
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )
    app_name: str = Field(default="autorag-test", alias="APP_NAME", description="Application name")

    # Environment configuration
    environment: Environment = Field(
        Environment.LOCAL,
        alias="ENVIRONMENT",
        description="Application environment",
    )

    firecrawl_api_key: str = Field(
        alias="FIRECRAWL_API_KEY",
        description="API key for Firecrawl service",
    )

    r2_access_key_id: str = Field(
        alias="R2_ACCESS_KEY_ID",
        description="Access key ID for R2 storage",
    )

    r2_secret_access_key: str = Field(
        alias="R2_SECRET_ACCESS_KEY",
        description="Secret access key for R2 storage",
    )

    r2_bucket_name: str = Field(
        default="test-bucket",
        alias="R2_BUCKET_NAME",
        description="Name of the R2 bucket",
    )

    r2_account_id: str = Field(
        alias="R2_ACCOUNT_ID",
        description="Account ID for R2 storage",
    )

    # Debug
    debug: bool | None = Field(
        default=None,
        description="True if debug mode is enabled. Defaults to True in local environment, False otherwise.",
        alias="DEBUG",
    )

    @model_validator(mode="after")
    def set_debug(self) -> Self:
        if self.debug is None:
            self.debug = self.environment == Environment.LOCAL
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore


settings = get_settings()
