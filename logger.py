import logging
import os
import sys

from settings import settings


def is_github_actions() -> bool:
    """
    Detect if the application is running in GitHub Actions.

    Returns:
        bool: True if running in GitHub Actions, False otherwise
    """
    return bool(os.environ.get("GITHUB_ACTIONS"))


def is_test_environment() -> bool:
    """
    Detect if the application is running in a test environment.

    Returns:
        bool: True if running in a test environment, False otherwise
    """
    # Check for pytest or other test frameworks
    return "pytest" in sys.modules or bool(os.environ.get("PYTEST_CURRENT_TEST"))


class ConsoleFormatter(logging.Formatter):
    """
    Define ab optimal format for my logger
    Create instance
    Return it for use
    """

    def __init__(self) -> None:
        format = "%(asctime)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s"
        datefmt = "%Y-%m-%d %H:%M:%S"  # Optional: cleaner date format
        super().__init__(format, datefmt=datefmt)


def configure_logging() -> None:
    """
    Configure the logging system for the application.

    This should be called ONCE at application startup.

    Args:
        enable_console: Whether to enable console logging
    """
    # 1. Get the top-level application logger (NOT the root logger)
    app_logger = logging.getLogger(settings.app_name)
    log_level = logging.DEBUG if settings.debug else logging.INFO
    app_logger.setLevel(log_level)  # Set level on the app logger

    # Remove existing handlers to avoid duplicates
    for handler in app_logger.handlers[:]:
        app_logger.removeHandler(handler)

    # Setup console logger
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(ConsoleFormatter())
    app_logger.addHandler(console_handler)

    # Add Logfire handler for WARNING+ logs only
    # logfire_handler = logfire.LogfireLoggingHandler()
    # logfire_handler.setLevel(logging.WARNING)  # Only send warnings and above
    # app_logger.addHandler(logfire_handler)

    # Skip Sentry initialization in test environments or GitHub Actions
    # if is_test_environment() or is_github_actions():
    #     logging.info("Skipping Sentry initialization in test/CI environment")
    # # Initialize Sentry with built-in integrations in non-test environments
    # elif settings.sentry_dsn:
    #     sentry_sdk.init(
    #         dsn=settings.sentry_dsn,
    #         send_default_pii=True,
    #         traces_sample_rate=1.0 if settings.debug else 0.1,  # Reduce sampling in production
    #         _experiments={"continuous_profiling_auto_start": True},
    #         environment=settings.environment.value,
    #     )
    # else:
    #     # Log a warning if Sentry DSN is missing in non-test, non-CI environment
    #     logging.warning("Sentry DSN not configured. Error tracking is disabled.")

    # Suppress noisy third-party loggers
    logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.ERROR)
    logging.getLogger("httpx._client").setLevel(logging.ERROR)  # Client internals
    logging.getLogger("httpx._trace").setLevel(logging.ERROR)  # Trace logs like receive_response_body
    logging.getLogger("logfire").setLevel(logging.ERROR)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.

    This does NOT configure the logging system - it just returns a logger.
    Call configure_logging() first at application startup.

    Args:
        The name of the logger.

    Returns:
        A configured logger instance
    """
    name = f"{settings.app_name}.{name}"
    logger = logging.getLogger(name)

    # Add a null handler if no handlers are configured yet
    # This prevents "No handlers could be found" warnings
    if not logger.handlers and not logging.root.handlers:
        logger.addHandler(logging.NullHandler())

    return logger
