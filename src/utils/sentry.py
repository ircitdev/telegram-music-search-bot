"""Sentry error tracking integration."""
import sentry_sdk
from sentry_sdk.integrations.aiohttp import AioHttpIntegration

from src.config import settings
from src.utils.logger import logger


def init_sentry():
    """Initialize Sentry error tracking if DSN is configured."""
    if not settings.SENTRY_DSN:
        logger.info("Sentry DSN not configured, error tracking disabled")
        return False

    try:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            integrations=[
                AioHttpIntegration(),
            ],
            # Set traces_sample_rate to 1.0 to capture 100% of transactions for performance monitoring
            traces_sample_rate=0.1,
            # Set profiles_sample_rate to 1.0 to profile 100% of sampled transactions
            profiles_sample_rate=0.1,
            # Environment
            environment="production",
            # Release version (can be set from env or git)
            release="musicfinder@1.0.0",
            # Additional options
            send_default_pii=False,  # Don't send personally identifiable information
            attach_stacktrace=True,
            # Filter sensitive data
            before_send=filter_sensitive_data,
        )
        logger.info("Sentry initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")
        return False


def filter_sensitive_data(event, hint):
    """Filter sensitive data before sending to Sentry."""
    # Remove sensitive request data
    if "request" in event:
        request = event["request"]
        if "headers" in request:
            # Remove authorization headers
            headers = request["headers"]
            for key in list(headers.keys()):
                if key.lower() in ("authorization", "cookie", "x-api-key"):
                    headers[key] = "[Filtered]"

    # Remove sensitive exception data
    if "exception" in event:
        for exception in event.get("exception", {}).get("values", []):
            if "stacktrace" in exception:
                for frame in exception["stacktrace"].get("frames", []):
                    # Filter local variables that might contain tokens
                    if "vars" in frame:
                        vars_dict = frame["vars"]
                        for key in list(vars_dict.keys()):
                            key_lower = key.lower()
                            if any(s in key_lower for s in ("token", "password", "secret", "key", "dsn")):
                                vars_dict[key] = "[Filtered]"

    return event


def capture_exception(error: Exception, **extra):
    """Capture exception and send to Sentry with extra context."""
    if not settings.SENTRY_DSN:
        return

    with sentry_sdk.push_scope() as scope:
        for key, value in extra.items():
            scope.set_extra(key, value)
        sentry_sdk.capture_exception(error)


def capture_message(message: str, level: str = "info", **extra):
    """Capture message and send to Sentry."""
    if not settings.SENTRY_DSN:
        return

    with sentry_sdk.push_scope() as scope:
        for key, value in extra.items():
            scope.set_extra(key, value)
        sentry_sdk.capture_message(message, level=level)


def set_user(user_id: int, username: str = None):
    """Set current user context for Sentry."""
    if not settings.SENTRY_DSN:
        return

    sentry_sdk.set_user({
        "id": str(user_id),
        "username": username,
    })


def set_tag(key: str, value: str):
    """Set a tag for current scope."""
    if not settings.SENTRY_DSN:
        return

    sentry_sdk.set_tag(key, value)
