import sentry_sdk

from sidekick import config, session


def _before_send(event, hint):
    """Filter sensitive data from Sentry events."""
    # Don't send events if telemetry is disabled
    if not session.telemetry_enabled:
        return None
    
    # Filter out sensitive information
    if event.get("request") and event["request"].get("headers"):
        # Remove authorization headers
        headers = event["request"]["headers"]
        for key in list(headers.keys()):
            if key.lower() in ("authorization", "cookie", "x-api-key"):
                headers[key] = "[Filtered]"
    
    # Filter environment variables
    if event.get("extra") and event["extra"].get("sys.argv"):
        args = event["extra"]["sys.argv"]
        # Filter any arguments that might contain API keys
        for i, arg in enumerate(args):
            if "key" in arg.lower() or "token" in arg.lower() or "secret" in arg.lower():
                args[i] = "[Filtered]"
    
    # Filter message content to ensure no sensitive data is leaked
    if event.get("extra") and event["extra"].get("message"):
        # Remove potential sensitive content from messages
        event["extra"]["message"] = "[Content Filtered]"
    
    return event


def setup_sentry():
    """Setup Sentry for error reporting if telemetry is enabled."""
    if not session.telemetry_enabled:
        return
    
    # Determine environment based on whether we're running in development or production
    environment = "development" if config.IS_DEV else "production"
    
    sentry_sdk.init(
        dsn='https://c967e1bebffe899093ed6bc2ee2e90c7@o171515.ingest.us.sentry.io/4509084774105088',
        traces_sample_rate=0.1,  # Sample only 10% of transactions
        profiles_sample_rate=0.1,  # Sample only 10% of profiles
        send_default_pii=False,  # Don't send personally identifiable information
        before_send=_before_send,  # Filter sensitive data
        environment=environment  # Set based on whether we're running from source or installed package
    )
    
    # Set user ID to anonymous session ID
    sentry_sdk.set_user({"id": session.session_id})
