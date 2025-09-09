"""Site-level configuration.

Centralizes values that may come from environment variables so the rest
of the codebase can import from a single place instead of calling
`os.getenv` scattered throughout the code.

Keep this file small and side-effect free.
"""
import os

# Public domain used in system prompts and links. Fallback matches previous behavior.
APP_DOMAIN = os.getenv("DOMAIN", "https://stackifier.com")

def get_app_domain() -> str:
    """Return configured application domain.

    This wrapper exists so callers can use a function if they prefer
    and so we have a single place to normalise the value in the future.
    """
    return APP_DOMAIN
