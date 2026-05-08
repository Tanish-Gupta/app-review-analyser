"""Central, typed configuration for the whole project.

Loaded from environment variables (or a local `.env` file). Each phase imports
`settings` from this module instead of reading env vars directly, so the
Vercel runtime, the CLI, and the test suite all see one source of truth.
"""

from __future__ import annotations

from email.utils import parseaddr
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[1]

MIN_WEEKS = 12
MAX_WEEKS = 26


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Source ---
    playstore_app_id: str = "com.nextbillion.groww"
    weeks_lookback: int = Field(default=MIN_WEEKS, ge=MIN_WEEKS, le=MAX_WEEKS)
    lang: str = "en"
    country: str = "in"

    # --- Storage paths (local dev) ---
    data_dir: Path = PROJECT_ROOT / "data"
    raw_dir: Path = PROJECT_ROOT / "data" / "raw"
    interim_dir: Path = PROJECT_ROOT / "data" / "interim"
    output_dir: Path = PROJECT_ROOT / "data" / "output"

    # --- LLM (Phase 3+) ---
    groq_api_key: str | None = None
    groq_model_reasoning: str = "llama-3.1-70b-versatile"
    groq_model_fast: str = "llama-3.1-8b-instant"
    phase3_max_rows: int = 1200
    phase3_batch_size: int = 8
    phase3_sample_size: int = 40

    # --- Email (Phase 5) ---
    email_mode: Literal["draft", "send", "both"] = "draft"
    # Verified "From" for Resend/SMTP (server-side only). Frontend supplies recipient separately.
    email_from: str | None = None
    # Optional default recipient for CLI/cron when no per-request recipient is passed.
    alert_email: str | None = None
    resend_api_key: str | None = None
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_pass: str | None = Field(
        default=None,
        validation_alias=AliasChoices("SMTP_PASS", "EMAIL_PASSWORD"),
    )

    # --- Vercel runtime (Phase 6) ---
    blob_read_write_token: str | None = None
    kv_url: str | None = None
    kv_rest_api_url: str | None = None
    kv_rest_api_token: str | None = None
    qstash_url: str = "https://qstash.upstash.io"
    qstash_token: str | None = None
    qstash_current_signing_key: str | None = None
    qstash_next_signing_key: str | None = None
    cron_secret: str | None = None

    # --- Local dev / observability ---
    run_local: bool = True
    log_level: str = "INFO"

    @field_validator("weeks_lookback")
    @classmethod
    def _enforce_min_weeks(cls, v: int) -> int:
        if v < MIN_WEEKS:
            return MIN_WEEKS
        return v

    @model_validator(mode="after")
    def _smtp_user_from_email_from(self) -> Settings:
        """If SMTP_USER is unset, use the address part of EMAIL_FROM (e.g. Gmail SMTP)."""
        if self.smtp_user and str(self.smtp_user).strip():
            return self
        if self.email_from and str(self.email_from).strip():
            _, addr = parseaddr(str(self.email_from).strip())
            if addr and "@" in addr:
                self.smtp_user = addr
        return self

    def ensure_dirs(self) -> None:
        for d in (self.data_dir, self.raw_dir, self.interim_dir, self.output_dir):
            d.mkdir(parents=True, exist_ok=True)


settings = Settings()
