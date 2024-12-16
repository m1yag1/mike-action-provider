import os
from dataclasses import dataclass, field

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


@lru_cache(maxsize=1, typed=True)
def get_config() -> Config:
    load_dotenv(dotenv_path="./local.env")
    return Config()
