import time
import hashlib
import uuid
from flask import request, has_request_context
from app import db, app
from .actions import LogAction
from .models import ActivityLog
import logging

logger = logging.getLogger("StudyBot")

def log_action(
        action: LogAction,
        user=None,
        value=None,
        context=None,
        strategy=None,
        turn=None,
        step=None,
        http_status=None,
        user_agent=None,
        include_ip=True
):
    """
    Central logging function for all activity in the system.

    Args:
        action (LogAction): The action being performed
        user (User): User object
        value (dict): Additional data as JSON
        context (str): Context
        strategy (str): Strategy
        turn (int): Conversation turn
        step (str): Conversation step
        http_status (int): HTTP status code
        user_agent (str): Override user agent
        include_ip (bool): Whether to hash IP

    Example:
        log_action(
            LogAction.START_CONVERSATION,
            user=user,
            value={"language": "en"},
            http_status=200
        )
    """
    try:
        extracted_user_agent = None
        ip = None

        if has_request_context():
            extracted_user_agent = user_agent or request.headers.get('User-Agent')

            if include_ip and request.remote_addr:
                ip = request.remote_addr

        log_entry = ActivityLog(
            id=str(uuid.uuid4()),
            timestamp=int(time.time()),
            user_id=user.id if user else None,
            user_client=user.client if user else None,
            action=action.value,
            value=value,
            user_agent=extracted_user_agent,
            ip_address=ip,
            context=context,
            strategy=strategy,
            turn=turn,
            step=step,
            http_status=http_status
        )

        db.session.add(log_entry)
        db.session.commit()

        logger.debug(f"Logged action: {action.value} for user {user.id if user else 'system'}")
        return log_entry

    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to log action {action}: {e}")
        return None

def log_api_call(endpoint: str, method: str = None, user=None):
    """Log API calls"""
    if has_request_context() and not method:
        method = request.method

    log_action(
        LogAction.API_CALL_START,
        user=user,
        value={"endpoint": endpoint, "method": method}
    )


def log_error(error: Exception, user=None, context: str = None):
    """Log errors with full context"""
    import traceback

    log_action(
        LogAction.ERROR_OCCURRED,
        user=user,
        value={
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
            "traceback": traceback.format_exc()
        },
        http_status=500
    )