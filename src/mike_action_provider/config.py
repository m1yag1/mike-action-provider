"""Application Configuration"""
import os
from dataclasses import dataclass, field
from pathlib import Path

from functools import lru_cache
from dotenv import load_dotenv


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
        default_factory=lambda: os.getenv("SQL_ECHO", "false").lower() == "true"
    )
    DB_PATH: Path = field(
        default_factory=lambda: Path(
            os.getenv("DB_PATH", "./data/actions.db")
        )
    )


@lru_cache(maxsize=1, typed=True)
def get_config() -> Config:
    """Get configuration settings.

    Returns:
        Config: Configuration settings.
    """
    load_dotenv(dotenv_path="./local.env")
    return Config()
