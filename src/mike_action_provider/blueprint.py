"""Flask blueprint for the action provider."""

import datetime as dt
import json
from flask import request
from pydantic import BaseModel, Field
from typing import Dict, Any

from globus_action_provider_tools import (
    ActionProviderDescription,
    ActionRequest,
    ActionStatus,
    ActionStatusValue,
    AuthState,
)
from globus_action_provider_tools.authorization import (
    authorize_action_access_or_404,
    authorize_action_management_or_404,
)
from globus_action_provider_tools.flask import ActionProviderBlueprint
from globus_action_provider_tools.flask.exceptions import ActionConflict, ActionNotFound
from globus_action_provider_tools.flask.types import (
    ActionCallbackReturn,
    ActionLogReturn,
)

from .config import get_config
from mike_action_provider.db.connection import get_db
from mike_action_provider.db.crud import (
    create_action_status,
    get_action_status,
    update_action_status,
)
from mike_action_provider.logging import get_logger
from mike_action_provider.utils import utc_now

logger = get_logger(__name__)


def _update_action_status(
    action_status: ActionStatus, request_body: Dict[str, Any]
) -> ActionStatus:
    """Update action status if it has exceeded the maximum sleep time.

    Args:
        action_status (ActionStatus): The action status to update.
        request_data (Dict[str, Any]): The original request data containing UTC offset.

    Returns:
        ActionStatus: The updated action status.
    """
    now = utc_now()
    # Ensure start_time is treated as UTC
    start_time = dt.datetime.fromisoformat(action_status.start_time)
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=dt.timezone.utc)
    time_diff = now - start_time
    total_seconds = time_diff.total_seconds()

    if total_seconds > get_config().MAX_SLEEP_TIME:
        logger.info(
            "Action completed",
            extra={
                "action_id": action_status.action_id,
                "duration_minutes": round(time_diff.total_seconds() / 60, 2),
            },
        )
        action_status.status = ActionStatusValue.SUCCEEDED
        action_status.display_status = "Action completed"
        action_status.completion_time = now.isoformat()

        if request_body.get("utc_offset"):
            offset_hours = int(request_body["utc_offset"])
            # For negative offsets, we need to subtract the hours
            if offset_hours < 0:
                local_time = start_time - dt.timedelta(hours=abs(offset_hours))
            else:
                local_time = start_time + dt.timedelta(hours=offset_hours)
            action_status.details = {
                "utc_offset": request_body["utc_offset"],
                "utc_time": start_time.isoformat(),
                "local_time": local_time.isoformat(),
            }

        with get_db() as db:
            update_action_status(
                db=db,
                action_id=action_status.action_id,
                status=action_status.status,
                display_status=action_status.display_status,
                completion_time=now,
                details=json.dumps(action_status.details),
            )
    return action_status


class ActionProviderInput(BaseModel):
    utc_offset: int = Field(
        ..., title="UTC Offset", description="An input value to this ActionProvider"
    )

    class Config:
        schema_extra = {"example": {"utc_offset": 10}}


description = ActionProviderDescription(
    globus_auth_scope=f"https://auth.globus.org/scopes/{get_config().CLIENT_ID}/action_all",
    title="What Time Is It Right Now?",
    admin_contact="support@whattimeisrightnow.example",
    synchronous=True,
    input_schema=ActionProviderInput,
    api_version="1.0",
    subtitle="Another exciting promotional tie-in for whattimeisitrightnow.com",
    description="",
    keywords=["time", "whattimeisitnow", "productivity"],
    visible_to=["public"],
    runnable_by=["all_authenticated_users"],
    administered_by=["support@whattimeisrightnow.example"],
)


aptb = ActionProviderBlueprint(
    name="apt",
    import_name=__name__,
    url_prefix="/apt",
    provider_description=description,
)


@aptb.action_run
def my_action_run(
    action_request: ActionRequest, auth: AuthState
) -> ActionCallbackReturn:
    """Implement custom business logic related to instantiating an Action here.

    Once launched, collect details on the Action and create an ActionStatus
    which records information on the instantiated Action and gets stored.
    """
    logger.info(
        "Creating new action",
        extra={
            "creator_id": auth.effective_identity,
            "label": action_request.label,
        },
    )

    current_utc = utc_now()
    action_status = ActionStatus(
        status=ActionStatusValue.ACTIVE,
        creator_id=str(auth.effective_identity),
        label=action_request.label or None,
        monitor_by=action_request.monitor_by or auth.identities,
        manage_by=action_request.manage_by or auth.identities,
        start_time=current_utc.isoformat(),
        completion_time=None,
        release_after=action_request.release_after or "P30D",
        display_status=ActionStatusValue.ACTIVE,
        details={},
    )

    # Store in database
    with get_db() as db:
        create_action_status(
            db=db,
            action_id=action_status.action_id,
            status=action_status.status,
            creator_id=action_status.creator_id,
            monitor_by=",".join(action_status.monitor_by),
            manage_by=",".join(action_status.manage_by),
            release_after=str(action_status.release_after),
            display_status=action_status.display_status,
            request_json=request.get_json(),
            label=action_status.label,
            details=action_status.details,
        )
        logger.info(
            "Action created successfully",
            extra={"action_id": action_status.action_id},
        )

    return action_status


@aptb.action_status
def my_action_status(action_id: str, auth: AuthState) -> ActionCallbackReturn:
    """Query for the action_id in the database to return the up-to-date ActionStatus.

    We will determine if the action has exceeded MAX_SLEEP_TIME,
    if so, the action status will be changed to SUCCEEDED.
    """
    logger.debug("Checking action status", extra={"action_id": action_id})
    with get_db() as db:
        db_action = get_action_status(db, action_id)
        if db_action is None:
            logger.warning("Action not found", extra={"action_id": action_id})
            raise ActionNotFound(f"No action with {action_id}")

        action_status = ActionStatus(
            action_id=db_action.action_id,
            status=db_action.status,
            creator_id=db_action.creator_id,
            label=db_action.label,
            monitor_by=set(db_action.monitor_by.split(",")),
            manage_by=set(db_action.manage_by.split(",")),
            start_time=db_action.start_time.isoformat(),
            completion_time=(
                db_action.completion_time.replace(tzinfo=dt.timezone.utc).isoformat()
                if db_action.completion_time
                else None
            ),
            release_after=db_action.release_after,
            display_status=db_action.display_status[:64],
            details=json.loads(db_action.details) if db_action.details else {},
        )

        authorize_action_access_or_404(action_status, auth)
        if action_status.status == ActionStatusValue.ACTIVE:
            request_data = db_action.request_json
            action_status = _update_action_status(
                action_status, request_data.get("body")
            )
        logger.debug(
            "Action status retrieved",
            extra={
                "action_id": action_id,
                "status": action_status.status,
            },
        )
        return action_status


@aptb.action_cancel
def my_action_cancel(action_id: str, auth: AuthState) -> ActionCallbackReturn:
    """Cancel an action.

    Only Actions that are not in a completed state may be cancelled.
    Cancellations do not necessarily require that an Action's execution be
    stopped. Once cancelled, the ActionStatus object should be updated and
    stored.
    """
    logger.info("Cancelling action", extra={"action_id": action_id})
    with get_db() as db:
        db_action = get_action_status(db, action_id)
        if db_action is None:
            logger.warning("Action not found", extra={"action_id": action_id})
            raise ActionNotFound(f"No action with {action_id}")

        action_status = ActionStatus(
            action_id=db_action.action_id,
            status=db_action.status,
            creator_id=db_action.creator_id,
            label=db_action.label,
            monitor_by=set(db_action.monitor_by.split(",")),
            manage_by=set(db_action.manage_by.split(",")),
            start_time=db_action.start_time.isoformat(),
            completion_time=(
                db_action.completion_time.replace(tzinfo=dt.timezone.utc).isoformat()
                if db_action.completion_time
                else None
            ),
            release_after=db_action.release_after,
            display_status=db_action.display_status[:64],
            details=db_action.details,
        )

        authorize_action_management_or_404(action_status, auth)
        if action_status.is_complete():
            logger.warning(
                "Cannot cancel completed action",
                extra={
                    "action_id": action_id,
                    "status": action_status.status,
                },
            )
            raise ActionConflict("Cannot cancel complete action")

        action_status.status = ActionStatusValue.FAILED
        action_status.display_status = f"Cancelled by {auth.effective_identity}"

        update_action_status(
            db=db,
            action_id=action_id,
            status=action_status.status,
            display_status=action_status.display_status,
        )
        logger.info(
            "Action cancelled successfully",
            extra={
                "action_id": action_id,
                "cancelled_by": auth.effective_identity,
            },
        )
        return action_status


@aptb.action_release
def my_action_release(action_id: str, auth: AuthState) -> ActionCallbackReturn:
    """Release an action.

    Only Actions that are in a completed state may be released. The release
    operation marks the ActionStatus object as released in the data store.
    The final, up to date ActionStatus is returned after a successful release.
    """
    logger.info("Releasing action", extra={"action_id": action_id})
    with get_db() as db:
        db_action = get_action_status(db, action_id)
        if db_action is None:
            logger.warning("Action not found", extra={"action_id": action_id})
            raise ActionNotFound(f"No action with {action_id}")

        action_status = ActionStatus(
            action_id=db_action.action_id,
            status=db_action.status,
            creator_id=db_action.creator_id,
            label=db_action.label,
            monitor_by=set(db_action.monitor_by.split(",")),
            manage_by=set(db_action.manage_by.split(",")),
            start_time=db_action.start_time.isoformat(),
            completion_time=(
                db_action.completion_time.replace(tzinfo=dt.timezone.utc).isoformat()
                if db_action.completion_time
                else None
            ),
            release_after=db_action.release_after,
            display_status=db_action.display_status,
            details=json.loads(db_action.details) if db_action.details else {},
        )

        authorize_action_management_or_404(action_status, auth)
        if not action_status.is_complete():
            logger.warning(
                "Cannot release incomplete action",
                extra={
                    "action_id": action_id,
                    "status": action_status.status,
                },
            )
            raise ActionConflict("Cannot release incomplete Action")

        action_status.display_status = f"Released by {auth.effective_identity}"
        # We soft delete the action status by setting is_released to True
        update_action_status(
            db=db,
            action_id=action_id,
            display_status=action_status.display_status,
            is_released=True,
        )
        logger.info(
            "Action released successfully",
            extra={
                "action_id": action_id,
                "released_by": auth.effective_identity,
            },
        )
        return action_status
