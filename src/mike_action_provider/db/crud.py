"""CRUD operations for the action provider database."""

from typing import Optional, Dict, Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from mike_action_provider.db.models import ActionStatus
from mike_action_provider.utils import utc_now


def create_action_status(
    db: Session,
    action_id: str,
    status: str,
    creator_id: str,
    monitor_by: str,
    manage_by: str,
    release_after: str,
    display_status: str,
    request_json: Dict[str, Any],
    label: Optional[str] = None,
    details: str = "{}",
) -> ActionStatus:
    """Create a new action status record.

    Args:
        db: Database session
        action_id: Unique identifier for the action
        status: Current status of the action
        creator_id: ID of the user who created the action
        monitor_by: Comma-separated list of identities that can monitor
        manage_by: Comma-separated list of identities that can manage
        release_after: ISO 8601 duration string for release timing
        display_status: Human-readable status message
        request_json: The original JSON request that created this action
        label: Optional label for the action
        details: JSON string containing additional details

    Returns:
        ActionStatus: The created action status record
    """
    db_action = ActionStatus(
        action_id=action_id,
        status=status,
        creator_id=creator_id,
        label=label,
        monitor_by=monitor_by,
        manage_by=manage_by,
        start_time=utc_now(),
        release_after=release_after,
        display_status=display_status,
        details=details,
        request_json=request_json,
    )
    db.add(db_action)
    db.commit()
    db.refresh(db_action)
    return db_action


def get_action_status(db: Session, action_id: str) -> Optional[ActionStatus]:
    """Get an action status record by ID.

    Args:
        db: Database session
        action_id: Unique identifier for the action

    Returns:
        Optional[ActionStatus]: The action status record if found and not released,
            None otherwise
    """
    stmt = select(ActionStatus).where(
        ActionStatus.action_id == action_id,
        ActionStatus.is_released == False,
    )
    return db.scalar(stmt)


def update_action_status(
    db: Session,
    action_id: str,
    **kwargs: Any,
) -> Optional[ActionStatus]:
    """Update an action status record.

    Args:
        db: Database session
        action_id: Unique identifier for the action
        **kwargs: Fields to update and their new values

    Returns:
        Optional[ActionStatus]: The updated action status record if found,
            None otherwise
    """
    db_action = get_action_status(db, action_id)
    if not db_action:
        return None

    for key, value in kwargs.items():
        if hasattr(db_action, key):
            setattr(db_action, key, value)

    db.commit()
    db.refresh(db_action)
    return db_action


def delete_action_status(db: Session, action_id: str) -> bool:
    """Delete an action status record.

    Args:
        db: Database session
        action_id: Unique identifier for the action

    Returns:
        bool: True if the record was deleted, False if it wasn't found
    """
    db_action = get_action_status(db, action_id)
    if not db_action:
        return False

    db.delete(db_action)
    db.commit()
    return True
