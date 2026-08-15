"""
Shared helpers for the pipeline scripts:

- load_env_file(): reads `.env` from the project root (this file's directory),
  regardless of the caller's current working directory, and merges it with
  real environment variables (`os.environ` wins if a var is set in both).
- get_env(name, required=False): fetch a single var with a clear error.
- new_ssl_context(): a properly verifying SSL context for Buffer and RSS
  requests.

Previously each script duplicated a hand-rolled `.env` parser (all assuming
the script is launched from inside the project directory, which
silently breaks if run from elsewhere) and each also created an SSL context
with `check_hostname = False` / `verify_mode = CERT_NONE`, which disables
certificate validation entirely and exposes every API key sent over HTTPS
(Buffer) to man-in-the-middle interception.
This module fixes both issues in one place.
"""

import os
import ssl

_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
_ENV_PATH = os.path.join(_PROJECT_ROOT, ".env")

_cache = None


def load_env_file():
    """Parse `.env` (if present) and merge with the real process environment.

    Real environment variables always take precedence over `.env` file
    values, matching standard dotenv behavior.
    """
    global _cache
    if _cache is not None:
        return _cache

    env_vars = {}
    if os.path.exists(_ENV_PATH):
        with open(_ENV_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    env_vars[key.strip()] = val.strip().strip('"').strip("'")

    # Real env vars win over .env file values.
    env_vars.update({k: v for k, v in os.environ.items() if v})
    _cache = env_vars
    return env_vars


def get_env(name, required=False):
    value = load_env_file().get(name)
    if required and not value:
        raise RuntimeError(
            f"{name} not found. Set it in {_ENV_PATH} or export it as an environment variable."
        )
    return value


def new_ssl_context():
    """Return a default, properly-verifying SSL context.

    If you hit SSLCertVerificationError, the fix is almost always to point
    Python at a valid CA bundle (e.g. `pip install certifi` and set
    `SSL_CERT_FILE`), NOT to disable verification.
    """
    return ssl.create_default_context()
