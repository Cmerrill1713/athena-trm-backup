# common/secrets.py
"""
Secure secrets management with keychain fallback
Prefers macOS keychain over environment variables for production
"""
import os

try:
    import keyring
except ImportError:
    keyring = None

def load_secret(key: str, env: str, default: str = "") -> str:
    """
    Load secret from keychain first, then env var, then default

    Args:
        key: Keychain key name (e.g., "uat_token")
        env: Environment variable name (e.g., "UAT_TOKEN")
        default: Default value if not found

    Returns:
        Secret value

    Example:
        UAT_TOKEN = load_secret("uat_token", "UAT_TOKEN", "")

    Store in keychain (macOS):
        security add-generic-password -a stack -s "uat_token" -w "supersecret"
    """
    if keyring:
        try:
            v = keyring.get_password("stack-orchestration", key)
            if v:
                return v
        except Exception:
            pass

    return os.getenv(env, default)
