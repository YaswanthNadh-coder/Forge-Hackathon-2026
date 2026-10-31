"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Central configuration for Ayushman-Shield backend."""

    # Application
    app_name: str = "Ayushman-Shield"
    app_version: str = "1.0.0"
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Google Gemini
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    gemini_model: str = "gemini-2.5-pro"

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "hbp_2022_packages"

    # Sarvam AI
    sarvam_api_key: str = Field(default="", alias="SARVAM_API_KEY")
    sarvam_base_url: str = "https://api.sarvam.ai"

    # Playwright
    playwright_headless: bool = False
    cgrms_url: str = "https://cgrms.pmjay.gov.in"

    # File Storage
    upload_dir: str = "./uploads"
    reports_dir: str = "./reports"
    voice_dir: str = "./voice_outputs"

    # Rate Limits
    max_upload_size_mb: int = 20

    @property
    def has_gemini_key(self) -> bool:
        """Checks if a valid, non-placeholder Gemini API key is configured."""
        k = (self.gemini_api_key or "").strip()
        return bool(k and not k.startswith("your_") and "dummy" not in k.lower() and len(k) > 15)

    @property
    def has_sarvam_key(self) -> bool:
        """Checks if a valid, non-placeholder Sarvam API key is configured."""
        k = (self.sarvam_api_key or "").strip()
        return bool(k and not k.startswith("your_") and "dummy" not in k.lower() and len(k) > 15)

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
