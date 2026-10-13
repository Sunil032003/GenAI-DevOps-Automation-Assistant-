"""
Production Configuration for Forward Deployment Engineer (FDE) System.
"""

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()


@dataclass
class FDEConfig:
    """Runtime configuration for the multi-agent system."""

    # LLM Settings
    api_key: str = field(
        default_factory=lambda: os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY", "")
    )
    base_url: str = field(
        default_factory=lambda: os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    )
    primary_model: str = field(
        default_factory=lambda: os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
    )
    fallback_model: str = field(
        default_factory=lambda: os.getenv("FALLBACK_MODEL", "openrouter/free")
    )
    temperature: float = 0.1
    max_tokens: int = field(
        default_factory=lambda: int(os.getenv("MAX_TOKENS", "8192"))
    )
    request_timeout: int = field(
        default_factory=lambda: int(os.getenv("REQUEST_TIMEOUT", "90"))
    )

    # Operational Settings
    max_repair_attempts: int = field(
        default_factory=lambda: int(os.getenv("MAX_REPAIR_ATTEMPTS", "3"))
    )
    test_timeout_seconds: int = field(
        default_factory=lambda: int(os.getenv("TEST_TIMEOUT_SECONDS", "45"))
    )
    backup_source_files: bool = True
    auto_approve: bool = field(
        default_factory=lambda: os.getenv("AUTO_APPROVE", "false").lower() in ("true", "1", "yes")
    )

    # Deployment / Git Settings
    github_token: str = field(
        default_factory=lambda: os.getenv("GITHUB_TOKEN", "")
    )
    git_pilot_user: str = field(
        default_factory=lambda: os.getenv("GIT_USER", "FDE-Bot")
    )

    def validate(self) -> None:
        """Validate critical configuration settings."""
        if not self.api_key:
            raise ValueError(
                "Missing API key! Please set OPENROUTER_API_KEY or OPENAI_API_KEY in your .env file."
            )


# Default global configuration instance
config = FDEConfig()

