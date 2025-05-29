"""Application Configuration"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from functools import lru_cache
from dotenv import load_dotenv


TRUE_VALUES = {"True", "true", "1", "yes", "Y", "T"}


@dataclass
class Config:
    """Application Configuration"""

    CLIENT_ID: str = field(
        default_factory=lambda: os.getenv("GLOBUS_CLIENT_ID", "bogus")
    )
    CLIENT_SECRET: str = field(
        default_factory=lambda: os.getenv("GLOBUS_CLIENT_SECRET", "bogus")
    )
    SQL_ECHO: bool = field(
        default_factory=lambda: os.getenv("SQL_ECHO", "false") in TRUE_VALUES
    )
    DB_PATH: Path = field(
        default_factory=lambda: Path(os.getenv("DB_PATH", "./data/actions.db"))
    )
    # Logging configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "DEBUG")
    ENABLE_FILE_LOGGING: bool = field(
        default_factory=lambda: os.getenv("ENABLE_FILE_LOGGING", "false") in TRUE_VALUES
    )
    LOG_FILE: Optional[str] = field(
        default_factory=lambda: (
            os.getenv("LOG_FILE", "logs/action_provider.log")
            if os.getenv("ENABLE_FILE_LOGGING", "false") in TRUE_VALUES
            else None
        )
    )
    # Maximum time in seconds before an action is considered complete.
    # This is used to demonstrate how Flows will poll the action provider.
    MAX_SLEEP_TIME: int = field(
        default_factory=lambda: int(os.getenv("MAX_SLEEP_TIME", "120"))
    )


@lru_cache(maxsize=1, typed=True)
def get_config() -> Config:
    """Get configuration settings.

    Returns:
        Config: Configuration settings.
    """
    load_dotenv(dotenv_path="./local.env")
    return Config()
