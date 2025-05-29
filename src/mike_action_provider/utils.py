"""Utility functions for the action provider."""

import datetime as dt


def utc_now() -> dt.datetime:
    """Get current UTC time.

    Returns:
        dt.datetime: Current UTC time with timezone information.
    """
    return dt.datetime.now(dt.timezone.utc)
