import os

import sentry_sdk

from sidekick import session


def _before_send(event, hint):
    """Filter sensitive data from Sentry events."""
    if not session.telemetry_enabled:
        return None

    if event.get("request") and event["request"].get("headers"):
        headers = event["request"]["headers"]
        for key in list(headers.keys()):
            if key.lower() in ("authorization", "cookie", "x-api-key"):
                headers[key] = "[Filtered]"

    if event.get("extra") and event["extra"].get("sys.argv"):
        args = event["extra"]["sys.argv"]
        for i, arg in enumerate(args):
            if "key" in arg.lower() or "token" in arg.lower() or "secret" in arg.lower():
                args[i] = "[Filtered]"

    if event.get("extra") and event["extra"].get("message"):
        event["extra"]["message"] = "[Content Filtered]"

    return event


def setup():
    """Setup Sentry for error reporting if telemetry is enabled."""
    if not session.telemetry_enabled:
        return

    IS_DEV = os.environ.get("IS_DEV", False) == "True"
    environment = "development" if IS_DEV else "production"

    sentry_sdk.init(
        dsn="https://c967e1bebffe899093ed6bc2ee2e90c7@o171515.ingest.us.sentry.io/4509084774105088",
        traces_sample_rate=0.1,  # Sample only 10% of transactions
        profiles_sample_rate=0.1,  # Sample only 10% of profiles
        send_default_pii=False,  # Don't send personally identifiable information
        before_send=_before_send,  # Filter sensitive data
        environment=environment,
        debug=False,
        shutdown_timeout=0,
    )

    sentry_sdk.set_user({"id": session.device_id, "session_id": session.session_id})


def capture_exception(*args, **kwargs):
    return sentry_sdk.capture_exception(*args, **kwargs)
