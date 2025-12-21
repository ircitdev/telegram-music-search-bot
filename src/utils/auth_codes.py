"""Auth codes management for web dashboard authentication."""
import secrets
import time
import json
import os
from pathlib import Path

# File to store auth codes (shared between bot and dashboard API)
AUTH_CODES_FILE = Path(__file__).parent.parent.parent / "data" / "auth_codes.json"


def _load_codes() -> dict:
    """Load auth codes from file."""
    try:
        if AUTH_CODES_FILE.exists():
            with open(AUTH_CODES_FILE, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _save_codes(codes: dict):
    """Save auth codes to file."""
    try:
        AUTH_CODES_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(AUTH_CODES_FILE, 'w') as f:
            json.dump(codes, f)
    except Exception as e:
        print(f"Error saving auth codes: {e}")


def generate_auth_code(user_id: int, username: str = None) -> str:
    """Generate one-time auth code for admin."""
    codes = _load_codes()
    current_time = time.time()

    # Clean expired codes
    codes = {k: v for k, v in codes.items() if v.get("expires", 0) > current_time}

    # Generate new code
    code = secrets.token_urlsafe(32)
    codes[code] = {
        "user_id": user_id,
        "username": username,
        "expires": current_time + 300,  # 5 minutes
        "used": False,
        "created_at": current_time
    }

    _save_codes(codes)
    return code


def verify_auth_code(code: str) -> dict:
    """Verify auth code and return user info if valid."""
    codes = _load_codes()

    if code not in codes:
        return None

    auth_data = codes[code]
    current_time = time.time()

    # Check if expired
    if auth_data.get("expires", 0) < current_time:
        del codes[code]
        _save_codes(codes)
        return None

    # Check if already used
    if auth_data.get("used", False):
        return None

    # Mark as used
    codes[code]["used"] = True
    _save_codes(codes)

    # Generate session token
    session_token = secrets.token_urlsafe(48)

    return {
        "user_id": auth_data["user_id"],
        "username": auth_data.get("username"),
        "is_admin": True,
        "session_token": session_token
    }


def create_session(user_id: int, username: str = None) -> str:
    """Create a session token for authenticated admin."""
    codes = _load_codes()
    current_time = time.time()

    # Generate session token
    session_token = secrets.token_urlsafe(48)

    # Store session (expires in 24 hours)
    codes[f"session_{session_token}"] = {
        "user_id": user_id,
        "username": username,
        "is_admin": True,
        "expires": current_time + 86400,  # 24 hours
        "type": "session"
    }

    _save_codes(codes)
    return session_token


def verify_session(token: str) -> dict:
    """Verify session token."""
    codes = _load_codes()
    session_key = f"session_{token}"

    if session_key not in codes:
        return None

    session_data = codes[session_key]
    current_time = time.time()

    # Check if expired
    if session_data.get("expires", 0) < current_time:
        del codes[session_key]
        _save_codes(codes)
        return None

    return {
        "user_id": session_data["user_id"],
        "username": session_data.get("username"),
        "is_admin": session_data.get("is_admin", True)
    }


def invalidate_session(token: str):
    """Invalidate a session token."""
    codes = _load_codes()
    session_key = f"session_{token}"

    if session_key in codes:
        del codes[session_key]
        _save_codes(codes)
