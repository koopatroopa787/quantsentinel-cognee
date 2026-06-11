"""Application configuration and environment validation."""

from __future__ import annotations

from typing import Any

from pydantic import Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Populate os.environ with .env contents so other libraries can see them
load_dotenv()

class Settings(BaseSettings):
    """Strongly-typed runtime settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Google Cloud / Vertex AI
    GOOGLE_CLOUD_PROJECT: str
    GOOGLE_CLOUD_LOCATION: str
    GOOGLE_GENAI_USE_VERTEXAI: str = "TRUE"

    # Optional direct Gemini API key (used when not on Vertex AI)
    GEMINI_API_KEY: str = Field(default="")
    GOOGLE_API_KEY: str = Field(default="")  # alias recognised by google-genai

    # Phoenix Cloud
    PHOENIX_API_KEY: str
    PHOENIX_COLLECTOR_ENDPOINT: str
    PHOENIX_BASE_URL: str = "https://app.phoenix.arize.com"
    PHOENIX_PROJECT_NAME: str = "quantsentinel"

    # External data APIs
    FRED_API_KEY: str

    # App runtime settings
    CORS_ORIGINS: str = "http://localhost:3000"
    LOG_LEVEL: str = "INFO"
    MAX_BACKTEST_ROWS: int = 50000
    EVAL_SCORE_THRESHOLD: float = 0.70
    MAX_CRITIQUE_LOOPS: int = 3

    # Nightly optimizer model override
    OPTIMIZER_MODEL: str = "gemini-3-flash-preview"

    @field_validator("CORS_ORIGINS")
    @classmethod
    def validate_cors_origins(cls, value: str) -> str:
        """Validate that CORS origins are provided as a non-empty string."""
        if not value.strip():
            raise ValueError("CORS_ORIGINS cannot be empty")
        return value

    def cors_origins_list(self) -> list[str]:
        """Return CORS origins as a normalised list."""
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    def is_vertex_ai(self) -> bool:
        """Return True when configured to use Vertex AI rather than direct Gemini API."""
        return self.GOOGLE_GENAI_USE_VERTEXAI.upper() == "TRUE"


def _missing_fields(error: ValidationError) -> list[str]:
    """Extract missing required field names from a Pydantic validation error."""
    missing: list[str] = []
    for issue in error.errors():
        if issue.get("type") == "missing":
            location: tuple[Any, ...] = issue.get("loc", ())
            if location:
                missing.append(str(location[0]))
    return sorted(set(missing))


def load_settings() -> Settings:
    """Load settings and raise a runtime-friendly error for missing variables."""
    try:
        return Settings()
    except ValidationError as error:
        missing = _missing_fields(error)
        if missing:
            names = ", ".join(missing)
            raise RuntimeError(f"Missing required environment variables: {names}") from error
        raise RuntimeError(f"Invalid environment configuration: {error}") from error


settings = load_settings()
