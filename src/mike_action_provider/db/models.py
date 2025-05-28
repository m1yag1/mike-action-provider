"""SQLAlchemy models for the action provider."""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class ActionStatus(Base):
    """SQLAlchemy model for storing action statuses.

    This model represents the persistent storage of action statuses in the
    database.
    It maps directly to the ActionStatus objects used by the action provider.

    Attributes:
        action_id (str): Unique identifier for the action
        status (str): Current status of the action
        creator_id (str): ID of the user who created the action
        label (Optional[str]): Optional label for the action
        monitor_by (str): Comma-separated list of identities that can monitor
        manage_by (str): Comma-separated list of identities that can manage
        start_time (datetime): When the action was started
        completion_time (Optional[datetime]): When the action was completed
        release_after (str): ISO 8601 duration string for release timing
        display_status (str): Human-readable status message
        details (str): JSON string containing additional details
        request_json (dict): The original JSON request that created this action
        is_released (bool): Indicates whether the action is released
    """
    __tablename__ = "action_statuses"

    action_id: Mapped[str] = mapped_column(String, primary_key=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    creator_id: Mapped[str] = mapped_column(String, nullable=False)
    label: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    monitor_by: Mapped[str] = mapped_column(String, nullable=False)
    manage_by: Mapped[str] = mapped_column(String, nullable=False)
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    completion_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    release_after: Mapped[str] = mapped_column(String, nullable=False)
    display_status: Mapped[str] = mapped_column(String, nullable=False)
    details: Mapped[str] = mapped_column(String, nullable=False, default="{}")
    request_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    is_released: Mapped[bool] = mapped_column(default=False, nullable=False)
