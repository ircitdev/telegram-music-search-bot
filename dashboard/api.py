"""Dashboard API for MusicFinder analytics and administration."""
import os
import sys
import json
import secrets
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, Depends, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import aiosqlite

app = FastAPI(title="MusicFinder Admin Dashboard API", version="2.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Token Auth
security = HTTPBearer(auto_error=False)

# Load from env or use default
ENV_FILE = os.getenv("ENV_FILE", "/root/uspmusic-bot/.env")
DATABASE_PATH = os.getenv("DATABASE_PATH", "/root/uspmusic-bot/data/database.db")
AUTH_CODES_FILE = Path("/root/uspmusic-bot/data/auth_codes.json")


# ============== Telegram Auth System ==============

def _load_auth_codes() -> dict:
    """Load auth codes from file."""
    try:
        if AUTH_CODES_FILE.exists():
            with open(AUTH_CODES_FILE, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _save_auth_codes(codes: dict):
    """Save auth codes to file."""
    try:
        AUTH_CODES_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(AUTH_CODES_FILE, 'w') as f:
            json.dump(codes, f)
    except Exception as e:
        print(f"Error saving auth codes: {e}")


def verify_telegram_code(code: str) -> dict:
    """Verify Telegram auth code and return session token if valid."""
    codes = _load_auth_codes()

    if code not in codes:
        return None

    auth_data = codes[code]
    current_time = time.time()

    # Check if expired
    if auth_data.get("expires", 0) < current_time:
        del codes[code]
        _save_auth_codes(codes)
        return None

    # Check if already used
    if auth_data.get("used", False):
        return None

    # Mark as used
    codes[code]["used"] = True

    # Generate session token (valid for 24 hours)
    session_token = secrets.token_urlsafe(48)
    codes[f"session_{session_token}"] = {
        "user_id": auth_data["user_id"],
        "username": auth_data.get("username"),
        "is_admin": True,
        "expires": current_time + 86400,  # 24 hours
        "type": "session"
    }

    _save_auth_codes(codes)

    return {
        "user_id": auth_data["user_id"],
        "username": auth_data.get("username"),
        "session_token": session_token
    }


def verify_session_token(token: str) -> dict:
    """Verify session token."""
    codes = _load_auth_codes()
    session_key = f"session_{token}"

    if session_key not in codes:
        return None

    session_data = codes[session_key]
    current_time = time.time()

    # Check if expired
    if session_data.get("expires", 0) < current_time:
        del codes[session_key]
        _save_auth_codes(codes)
        return None

    return {
        "user_id": session_data["user_id"],
        "username": session_data.get("username"),
        "is_admin": session_data.get("is_admin", True)
    }


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify session token from Authorization header."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = credentials.credentials
    user_data = verify_session_token(token)

    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    return user_data


# ============== Auth Endpoints ==============

class AuthRequest(BaseModel):
    code: str


@app.post("/api/auth/telegram")
async def auth_telegram(data: AuthRequest):
    """Authenticate with Telegram code."""
    result = verify_telegram_code(data.code)

    if not result:
        raise HTTPException(status_code=401, detail="Invalid or expired code. Get a new code from bot with /web_admin")

    return {
        "success": True,
        "user_id": result["user_id"],
        "username": result["username"],
        "session_token": result["session_token"]
    }


@app.post("/api/auth/logout")
async def auth_logout(user: dict = Depends(verify_token)):
    """Logout and invalidate session."""
    # Session will expire naturally
    return {"success": True}


async def get_db():
    """Get database connection."""
    db = await aiosqlite.connect(DATABASE_PATH)
    db.row_factory = aiosqlite.Row
    return db


def read_env_file():
    """Read .env file and return as dict."""
    env_vars = {}
    try:
        if os.path.exists(ENV_FILE):
            with open(ENV_FILE, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        env_vars[key.strip()] = value.strip().strip('"')
    except Exception as e:
        print(f"Error reading .env: {e}")
    return env_vars


def write_env_file(env_vars: dict):
    """Write dict to .env file."""
    try:
        lines = []
        for key, value in env_vars.items():
            if " " in str(value) or "," in str(value):
                lines.append(f'{key}="{value}"')
            else:
                lines.append(f'{key}={value}')
        with open(ENV_FILE, 'w') as f:
            f.write("\n".join(lines) + "\n")
        return True
    except Exception as e:
        print(f"Error writing .env: {e}")
        return False


# ============== Overview Stats ==============

@app.get("/api/stats/overview")
async def get_overview(admin: str = Depends(verify_token)):
    """Get overview statistics."""
    db = await get_db()
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        # Total users
        cursor = await db.execute("SELECT COUNT(*) as count FROM users")
        total_users = (await cursor.fetchone())["count"]

        # Premium users
        cursor = await db.execute("SELECT COUNT(*) as count FROM users WHERE is_premium = 1")
        premium_users = (await cursor.fetchone())["count"]

        # Today's new users
        cursor = await db.execute(
            "SELECT COUNT(*) as count FROM users WHERE date(created_at) = ?", (today,)
        )
        new_users_today = (await cursor.fetchone())["count"]

        # Yesterday's new users (for comparison)
        cursor = await db.execute(
            "SELECT COUNT(*) as count FROM users WHERE date(created_at) = ?", (yesterday,)
        )
        new_users_yesterday = (await cursor.fetchone())["count"]

        # Total downloads
        cursor = await db.execute("SELECT COUNT(*) as count FROM downloads")
        total_downloads = (await cursor.fetchone())["count"]

        # Today's downloads
        cursor = await db.execute(
            "SELECT COUNT(*) as count FROM downloads WHERE date(downloaded_at) = ?", (today,)
        )
        downloads_today = (await cursor.fetchone())["count"]

        # Yesterday's downloads
        cursor = await db.execute(
            "SELECT COUNT(*) as count FROM downloads WHERE date(downloaded_at) = ?", (yesterday,)
        )
        downloads_yesterday = (await cursor.fetchone())["count"]

        # Total searches
        cursor = await db.execute("SELECT SUM(searches) as total FROM users")
        result = await cursor.fetchone()
        total_searches = result["total"] or 0

        # Total revenue (payments)
        cursor = await db.execute("SELECT SUM(amount) as total FROM payments WHERE currency = 'XTR'")
        result = await cursor.fetchone()
        total_revenue = result["total"] or 0

        # Today's revenue
        cursor = await db.execute(
            "SELECT SUM(amount) as total FROM payments WHERE date(created_at) = ? AND currency = 'XTR'",
            (today,)
        )
        result = await cursor.fetchone()
        revenue_today = result["total"] or 0

        # Active users (last 7 days)
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        cursor = await db.execute(
            "SELECT COUNT(DISTINCT user_id) as count FROM downloads WHERE date(downloaded_at) >= ?",
            (week_ago,)
        )
        active_users_week = (await cursor.fetchone())["count"]

        # Total referrals (count users with referred_by set)
        cursor = await db.execute("SELECT COUNT(*) as total FROM users WHERE referred_by IS NOT NULL")
        result = await cursor.fetchone()
        total_referrals = result["total"] or 0

        return {
            "total_users": total_users,
            "premium_users": premium_users,
            "new_users_today": new_users_today,
            "new_users_yesterday": new_users_yesterday,
            "total_downloads": total_downloads,
            "downloads_today": downloads_today,
            "downloads_yesterday": downloads_yesterday,
            "total_searches": total_searches,
            "total_revenue": total_revenue,
            "revenue_today": revenue_today,
            "active_users_week": active_users_week,
            "total_referrals": total_referrals
        }
    finally:
        await db.close()


# ============== User Statistics ==============

@app.get("/api/stats/users/growth")
async def get_users_growth(
    days: int = Query(30, ge=1, le=365),
    admin: str = Depends(verify_token)
):
    """Get user growth over time."""
    db = await get_db()
    try:
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        cursor = await db.execute("""
            SELECT date(created_at) as date, COUNT(*) as count
            FROM users
            WHERE date(created_at) >= ?
            GROUP BY date(created_at)
            ORDER BY date
        """, (start_date,))

        rows = await cursor.fetchall()
        return [{"date": row["date"], "count": row["count"]} for row in rows]
    finally:
        await db.close()


@app.get("/api/stats/users/list")
async def get_users_list(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    search: str = Query(None),
    filter_type: str = Query(None),  # premium, free, active, inactive
    admin: str = Depends(verify_token)
):
    """Get paginated users list."""
    db = await get_db()
    try:
        offset = (page - 1) * limit
        conditions = []
        params = []

        if search:
            conditions.append("(u.username LIKE ? OR CAST(u.id AS TEXT) LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%"])

        if filter_type == "premium":
            conditions.append("u.is_premium = 1")
        elif filter_type == "free":
            conditions.append("u.is_premium = 0")

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        # Get total count
        cursor = await db.execute(f"""
            SELECT COUNT(*) as count FROM users u WHERE {where_clause}
        """, params)
        total = (await cursor.fetchone())["count"]

        # Get users with stats
        cursor = await db.execute(f"""
            SELECT
                u.id as telegram_id,
                u.username,
                u.first_name,
                u.is_premium,
                u.premium_until,
                u.created_at,
                u.searches,
                u.bonus_downloads,
                u.referred_by,
                u.downloads as daily_downloads,
                (SELECT COUNT(*) FROM users r WHERE r.referred_by = u.id) as referral_count,
                u.downloads as total_downloads,
                u.last_seen as last_download
            FROM users u
            WHERE {where_clause}
            ORDER BY u.created_at DESC
            LIMIT ? OFFSET ?
        """, params + [limit, offset])

        rows = await cursor.fetchall()
        users = []
        for row in rows:
            user = dict(row)
            user["is_premium"] = bool(user["is_premium"])
            users.append(user)

        return {
            "users": users,
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit
        }
    finally:
        await db.close()


@app.get("/api/stats/users/{telegram_id}")
async def get_user_detail(
    telegram_id: int,
    admin: str = Depends(verify_token)
):
    """Get detailed user info."""
    db = await get_db()
    try:
        # User info
        cursor = await db.execute("""
            SELECT id as telegram_id, username, first_name, is_premium, premium_until,
                   bonus_downloads, searches, downloads, created_at, last_seen,
                   (SELECT COUNT(*) FROM users r WHERE r.referred_by = users.id) as referral_count,
                   downloads as daily_downloads
            FROM users WHERE id = ?
        """, (telegram_id,))
        user = await cursor.fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user_data = dict(user)
        user_data["is_premium"] = bool(user_data.get("is_premium"))

        # Downloads history
        cursor = await db.execute("""
            SELECT video_id, title, artist, downloaded_at
            FROM downloads
            WHERE user_id = ?
            ORDER BY downloaded_at DESC
            LIMIT 50
        """, (telegram_id,))
        downloads = [dict(row) for row in await cursor.fetchall()]

        # Favorites - table may not exist
        favorites = []
        try:
            cursor = await db.execute("""
                SELECT video_id, title, artist, added_at
                FROM favorites
                WHERE user_id = ?
                ORDER BY added_at DESC
            """, (telegram_id,))
            favorites = [dict(row) for row in await cursor.fetchall()]
        except:
            pass

        # Payments - table may not exist
        payments = []
        try:
            cursor = await db.execute("""
                SELECT amount, currency, payment_type, payload, created_at
                FROM payments
                WHERE user_id = ?
                ORDER BY created_at DESC
            """, (telegram_id,))
            payments = [dict(row) for row in await cursor.fetchall()]
        except:
            pass

        # Referrals
        cursor = await db.execute("""
            SELECT id as telegram_id, username, created_at
            FROM users
            WHERE referred_by = ?
            ORDER BY created_at DESC
        """, (telegram_id,))
        referrals = [dict(row) for row in await cursor.fetchall()]

        return {
            "user": user_data,
            "downloads": downloads,
            "favorites": favorites,
            "payments": payments,
            "referrals": referrals
        }
    finally:
        await db.close()


# ============== Downloads Statistics ==============

@app.get("/api/stats/downloads/daily")
async def get_downloads_daily(
    days: int = Query(30, ge=1, le=365),
    admin: str = Depends(verify_token)
):
    """Get daily downloads."""
    db = await get_db()
    try:
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        cursor = await db.execute("""
            SELECT date(downloaded_at) as date, COUNT(*) as count
            FROM downloads
            WHERE date(downloaded_at) >= ?
            GROUP BY date(downloaded_at)
            ORDER BY date
        """, (start_date,))

        rows = await cursor.fetchall()
        return [{"date": row["date"], "count": row["count"]} for row in rows]
    finally:
        await db.close()


@app.get("/api/stats/top-tracks")
async def get_top_tracks(
    limit: int = Query(20, ge=1, le=100),
    days: int = Query(None),
    admin: str = Depends(verify_token)
):
    """Get top downloaded tracks."""
    db = await get_db()
    try:
        params = []
        where_clause = ""

        if days:
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            where_clause = "WHERE date(downloaded_at) >= ?"
            params.append(start_date)

        cursor = await db.execute(f"""
            SELECT video_id, title, artist, COUNT(*) as downloads,
                   MAX(downloaded_at) as last_download
            FROM downloads
            {where_clause}
            GROUP BY video_id
            ORDER BY downloads DESC
            LIMIT ?
        """, params + [limit])

        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


@app.get("/api/stats/top-users")
async def get_top_users(
    limit: int = Query(20, ge=1, le=100),
    admin: str = Depends(verify_token)
):
    """Get most active users."""
    db = await get_db()
    try:
        cursor = await db.execute("""
            SELECT u.id as telegram_id, u.username, u.first_name, u.is_premium,
                   u.downloads, u.searches
            FROM users u
            ORDER BY u.downloads DESC
            LIMIT ?
        """, (limit,))

        rows = await cursor.fetchall()
        result = []
        for row in rows:
            user = dict(row)
            user["is_premium"] = bool(user["is_premium"])
            result.append(user)
        return result
    finally:
        await db.close()


@app.get("/api/stats/hourly")
async def get_hourly_activity(admin: str = Depends(verify_token)):
    """Get hourly activity distribution."""
    db = await get_db()
    try:
        cursor = await db.execute("""
            SELECT strftime('%H', downloaded_at) as hour, COUNT(*) as count
            FROM downloads
            WHERE date(downloaded_at) >= date('now', '-7 days')
            GROUP BY hour
            ORDER BY hour
        """)

        rows = await cursor.fetchall()
        return [{"hour": int(row["hour"]), "count": row["count"]} for row in rows]
    finally:
        await db.close()


# ============== Payments Statistics ==============

@app.get("/api/stats/payments")
async def get_payments(
    days: int = Query(30, ge=1, le=365),
    admin: str = Depends(verify_token)
):
    """Get payment statistics."""
    db = await get_db()
    try:
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        cursor = await db.execute("""
            SELECT date(created_at) as date,
                   SUM(amount) as total,
                   COUNT(*) as count,
                   payment_type
            FROM payments
            WHERE date(created_at) >= ?
            GROUP BY date(created_at), payment_type
            ORDER BY date
        """, (start_date,))

        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


@app.get("/api/stats/payments/list")
async def get_payments_list(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    admin: str = Depends(verify_token)
):
    """Get paginated payments list."""
    db = await get_db()
    try:
        offset = (page - 1) * limit

        cursor = await db.execute("SELECT COUNT(*) as count FROM payments")
        total = (await cursor.fetchone())["count"]

        cursor = await db.execute("""
            SELECT p.*, u.username, u.first_name
            FROM payments p
            LEFT JOIN users u ON p.user_id = u.id
            ORDER BY p.created_at DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))

        payments = [dict(row) for row in await cursor.fetchall()]

        return {
            "payments": payments,
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit
        }
    finally:
        await db.close()


# ============== Referrals Statistics ==============

@app.get("/api/stats/referrals")
async def get_referrals_stats(admin: str = Depends(verify_token)):
    """Get referral statistics."""
    db = await get_db()
    try:
        # Top referrers
        cursor = await db.execute("""
            SELECT u.id as telegram_id, u.username, u.first_name,
                   (SELECT COUNT(*) FROM users r WHERE r.referred_by = u.id) as referral_count
            FROM users u
            WHERE (SELECT COUNT(*) FROM users r WHERE r.referred_by = u.id) > 0
            ORDER BY referral_count DESC
            LIMIT 20
        """)
        top_referrers = [dict(row) for row in await cursor.fetchall()]

        # Referrals by day
        cursor = await db.execute("""
            SELECT date(created_at) as date, COUNT(*) as count
            FROM users
            WHERE referred_by IS NOT NULL
            AND date(created_at) >= date('now', '-30 days')
            GROUP BY date(created_at)
            ORDER BY date
        """)
        daily_referrals = [dict(row) for row in await cursor.fetchall()]

        # Total stats
        cursor = await db.execute("""
            SELECT
                COUNT(*) as total_referred,
                COUNT(DISTINCT referred_by) as total_referrers
            FROM users
            WHERE referred_by IS NOT NULL
        """)
        stats = dict(await cursor.fetchone())

        return {
            "top_referrers": top_referrers,
            "daily_referrals": daily_referrals,
            "total_referred": stats["total_referred"],
            "total_referrers": stats["total_referrers"]
        }
    finally:
        await db.close()


# ============== API Keys Management ==============

@app.get("/api/keys/list")
async def get_api_keys(admin: str = Depends(verify_token)):
    """Get all API keys with statistics."""
    db = await get_db()
    try:
        # Read current keys from .env
        env_vars = read_env_file()
        api_keys_str = env_vars.get("API_KEYS", "")

        keys = []
        if api_keys_str:
            for pair in api_keys_str.split(","):
                if ":" in pair:
                    name, key = pair.split(":", 1)
                    keys.append({
                        "name": name.strip(),
                        "key": key.strip()[:8] + "..." + key.strip()[-4:],
                        "key_full": key.strip()
                    })

        # Get API usage stats from database if table exists
        try:
            cursor = await db.execute("""
                SELECT api_key_name, COUNT(*) as requests,
                       MAX(created_at) as last_request
                FROM api_requests
                GROUP BY api_key_name
            """)
            stats = {row["api_key_name"]: dict(row) for row in await cursor.fetchall()}
        except:
            stats = {}

        # Merge stats with keys
        for key in keys:
            if key["name"] in stats:
                key["requests"] = stats[key["name"]]["requests"]
                key["last_request"] = stats[key["name"]]["last_request"]
            else:
                key["requests"] = 0
                key["last_request"] = None

        return {"keys": keys}
    finally:
        await db.close()


class ApiKeyCreate(BaseModel):
    name: str
    key: Optional[str] = None


@app.post("/api/keys/create")
async def create_api_key(data: ApiKeyCreate, admin: str = Depends(verify_token)):
    """Create new API key."""
    env_vars = read_env_file()
    api_keys_str = env_vars.get("API_KEYS", "")

    # Generate key if not provided
    key = data.key or secrets.token_urlsafe(24)

    # Add new key
    if api_keys_str:
        api_keys_str += f",{data.name}:{key}"
    else:
        api_keys_str = f"{data.name}:{key}"

    env_vars["API_KEYS"] = api_keys_str

    if write_env_file(env_vars):
        return {"success": True, "name": data.name, "key": key}
    else:
        raise HTTPException(status_code=500, detail="Failed to save key")


@app.delete("/api/keys/{name}")
async def delete_api_key(name: str, admin: str = Depends(verify_token)):
    """Delete API key."""
    env_vars = read_env_file()
    api_keys_str = env_vars.get("API_KEYS", "")

    if not api_keys_str:
        raise HTTPException(status_code=404, detail="No keys configured")

    # Filter out the key
    pairs = api_keys_str.split(",")
    new_pairs = [p for p in pairs if not p.strip().startswith(f"{name}:")]

    if len(pairs) == len(new_pairs):
        raise HTTPException(status_code=404, detail="Key not found")

    env_vars["API_KEYS"] = ",".join(new_pairs)

    if write_env_file(env_vars):
        return {"success": True}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete key")


@app.get("/api/keys/{name}/requests")
async def get_api_key_requests(
    name: str,
    limit: int = Query(100, ge=1, le=500),
    admin: str = Depends(verify_token)
):
    """Get API key request history."""
    db = await get_db()
    try:
        cursor = await db.execute("""
            SELECT * FROM api_requests
            WHERE api_key_name = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (name, limit))
        requests = [dict(row) for row in await cursor.fetchall()]
        return {"requests": requests}
    except:
        return {"requests": [], "error": "API requests table not found"}
    finally:
        await db.close()


# ============== Environment Configuration ==============

@app.get("/api/config")
async def get_config(admin: str = Depends(verify_token)):
    """Get current configuration (sensitive values masked)."""
    env_vars = read_env_file()

    # Mask sensitive values
    sensitive_keys = ["BOT_TOKEN", "CRYPTOBOT_TOKEN", "YOOKASSA_SECRET_KEY",
                      "AUDD_API_KEY", "LASTFM_API_KEY", "API_KEYS", "DASHBOARD_TOKENS"]

    config = {}
    for key, value in env_vars.items():
        if key in sensitive_keys and value:
            config[key] = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
        else:
            config[key] = value

    return {"config": config}


class ConfigUpdate(BaseModel):
    key: str
    value: str


@app.post("/api/config/update")
async def update_config(data: ConfigUpdate, admin: str = Depends(verify_token)):
    """Update configuration value."""
    env_vars = read_env_file()

    # Prevent updating critical keys
    critical_keys = ["BOT_TOKEN"]
    if data.key in critical_keys:
        raise HTTPException(status_code=403, detail="Cannot update critical config")

    env_vars[data.key] = data.value

    if write_env_file(env_vars):
        return {"success": True, "key": data.key}
    else:
        raise HTTPException(status_code=500, detail="Failed to update config")


# ============== User Management ==============

class UserPremiumUpdate(BaseModel):
    telegram_id: int
    is_premium: bool
    days: int = 30


@app.post("/api/users/set-premium")
async def set_user_premium(data: UserPremiumUpdate, admin: str = Depends(verify_token)):
    """Set user premium status."""
    db = await get_db()
    try:
        if data.is_premium:
            premium_until = datetime.now() + timedelta(days=data.days)
            await db.execute("""
                UPDATE users SET is_premium = 1, premium_until = ?
                WHERE id = ?
            """, (premium_until.isoformat(), data.telegram_id))
        else:
            await db.execute("""
                UPDATE users SET is_premium = 0, premium_until = NULL
                WHERE id = ?
            """, (data.telegram_id,))

        await db.commit()
        return {"success": True, "telegram_id": data.telegram_id}
    finally:
        await db.close()


class UserBonusUpdate(BaseModel):
    telegram_id: int
    bonus_downloads: int


@app.post("/api/users/set-bonus")
async def set_user_bonus(data: UserBonusUpdate, admin: str = Depends(verify_token)):
    """Set user bonus downloads."""
    db = await get_db()
    try:
        await db.execute("""
            UPDATE users SET bonus_downloads = ?
            WHERE id = ?
        """, (data.bonus_downloads, data.telegram_id))
        await db.commit()
        return {"success": True, "telegram_id": data.telegram_id}
    finally:
        await db.close()


# ============== System Info ==============

@app.get("/api/system/info")
async def get_system_info(admin: str = Depends(verify_token)):
    """Get system information."""
    import platform
    import psutil

    return {
        "platform": platform.system(),
        "python_version": platform.python_version(),
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint (no auth required)."""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


# ============== Initialize database tables for API logging ==============

async def init_db():
    """Initialize additional database tables."""
    db = await get_db()
    try:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS api_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_key_name TEXT NOT NULL,
                endpoint TEXT,
                query TEXT,
                target_chat_id TEXT,
                success INTEGER DEFAULT 1,
                error TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()
    except Exception as e:
        print(f"Error initializing db: {e}")
    finally:
        await db.close()


@app.on_event("startup")
async def startup():
    await init_db()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8085)
