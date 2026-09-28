import os
from pathlib import Path
import re

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ...database import get_app_meta_many, get_db, set_app_meta
from ...version import APP_VERSION
from ..security import admin_protection_status, require_admin_access

router = APIRouter()


def _env_any(*names: str) -> str:
    env = os.environ
    for name in names:
        for candidate in (name, name.lower(), name.upper()):
            value = env.get(candidate, "").strip()
            if value:
                return value
    lowered = {k.lower(): v for k, v in env.items()}
    for name in names:
        value = str(lowered.get(name.lower(), "")).strip()
        if value:
            return value
    meta_keys = [f"cfg:{name.lower()}" for name in names]
    meta = get_app_meta_many(meta_keys)
    for key in meta_keys:
        value = str(meta.get(key, "")).strip()
        if value:
            return value
    return ""


class SecretsUpdate(BaseModel):
    igdb_client_id: str | None = None
    igdb_client_secret: str | None = None
    ebay_client_id: str | None = None
    ebay_client_secret: str | None = None
    rawg_api_key: str | None = None
    pricecharting_token: str | None = None
    clear: list[str] = Field(default_factory=list)

class SchedulerUpdate(BaseModel):
    interval: int


class AutoBackupUpdate(BaseModel):
    enabled: bool = True
    retention: int = Field(default=14, ge=1, le=90)



_SECRET_FIELDS = {
    "igdb_client_id": "cfg:igdb_client_id",
    "igdb_client_secret": "cfg:igdb_client_secret",
    "ebay_client_id": "cfg:ebay_client_id",
    "ebay_client_secret": "cfg:ebay_client_secret",
    "rawg_api_key": "cfg:rawg_api_key",
    "pricecharting_token": "cfg:pricecharting_token",
}


def _human_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / 1024 / 1024:.1f} MB"


def _uploads_dir() -> str:
    default_uploads = "/app/uploads" if Path("/app").exists() else str(Path(__file__).resolve().parents[3] / "uploads")
    return os.getenv("UPLOADS_DIR", default_uploads)


def _safe_int(value, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _workflow_scheduler_status():
    repo_root = Path(__file__).resolve().parents[3]
    workflow_file = repo_root / ".github" / "workflows" / "daily-price-update.yml"
    if not workflow_file.exists():
        return {
            "scheduler_enabled": False,
            "scheduler_type": "manual",
            "scheduler_cron": None,
            "scheduler_source": None,
        }

    try:
        content = workflow_file.read_text(encoding="utf-8")
    except Exception:
        content = ""

    cron_match = re.search(r"cron:\s*(?:['\"]([^'\"]+)['\"]|([^\n#]+))", content)
    cron_expr = None
    if cron_match:
        cron_expr = (cron_match.group(1) or cron_match.group(2) or "").strip()
        if not cron_expr:
            cron_expr = None
    return {
        "scheduler_enabled": bool(cron_expr),
        "scheduler_type": "github_actions",
        "scheduler_cron": cron_expr,
        "scheduler_source": str(workflow_file.relative_to(repo_root)),
    }


@router.get("/api/settings/info")
async def settings_info():
    client_id = _env_any("IGDB_CLIENT_ID")
    pricecharting_token = _env_any("PRICECHARTING_TOKEN", "PRICE_CHARTING_TOKEN")
    ebay_client_id = _env_any("EBAY_CLIENT_ID", "EBAY_APP_ID", "EBAY_APPID", "EBAY_CLIENTID")
    ebay_client_secret = _env_any("EBAY_CLIENT_SECRET", "EBAY_SECRET", "EBAY_CLIENTSECRET", "EBAY_SECRET_KEY")
    rawg_key = _env_any("RAWG_API_KEY", "RAWG_KEY")
    db_path = os.getenv("DATABASE_URL", "sqlite:////app/app/data/games.db").replace("sqlite:///", "")
    try:
        db_size_bytes = os.path.getsize(db_path)
        db_size = _human_size(db_size_bytes)
    except Exception:
        db_size_bytes = 0
        db_size = "Unknown"

    uploads_dir = _uploads_dir()
    uploads_files = 0
    uploads_size_bytes = 0
    try:
        if os.path.isdir(uploads_dir):
            for root, _dirs, files in os.walk(uploads_dir):
                for name in files:
                    uploads_files += 1
                    try:
                        uploads_size_bytes += os.path.getsize(os.path.join(root, name))
                    except OSError:
                        pass
    except Exception:
        uploads_files = 0
        uploads_size_bytes = 0

    with get_db() as db:
        total_items = db.execute("SELECT COUNT(*) FROM games WHERE is_wishlist = 0").fetchone()[0]
        missing_covers = db.execute(
            "SELECT COUNT(*) FROM games WHERE (cover_url IS NULL OR cover_url = '') AND is_wishlist = 0"
        ).fetchone()[0]
        wishlist_count = db.execute("SELECT COUNT(*) FROM games WHERE is_wishlist = 1").fetchone()[0]
        platforms_count = db.execute("SELECT COUNT(*) FROM platforms").fetchone()[0]
        local_covers = db.execute(
            "SELECT COUNT(*) FROM games WHERE is_wishlist = 0 AND cover_url LIKE '/uploads/%'"
        ).fetchone()[0]
        remote_covers = db.execute(
            "SELECT COUNT(*) FROM games WHERE is_wishlist = 0 AND cover_url LIKE 'http%'"
        ).fetchone()[0]

        try:
            game_items = db.execute(
                """
                SELECT COUNT(*) FROM games
                WHERE is_wishlist = 0
                  AND (item_type = 'game' OR item_type IS NULL OR item_type = '')
                """
            ).fetchone()[0]
            non_game_items = db.execute(
                """
                SELECT COUNT(*) FROM games
                WHERE is_wishlist = 0
                  AND item_type IS NOT NULL
                  AND item_type != ''
                  AND item_type != 'game'
                """
            ).fetchone()[0]
        except Exception:
            game_items = total_items
            non_game_items = 0

    backup_dir = Path(db_path).parent / "backups"
    auto_backup_files = list(backup_dir.glob("collectabase-auto-backup-*.zip")) if backup_dir.is_dir() else []

    meta = get_app_meta_many(
        [
            "last_bulk_enrich_at",
            "last_bulk_enrich_success",
            "last_bulk_enrich_failed",
            "last_bulk_enrich_total",
            "last_bulk_price_update_at",
            "last_bulk_price_update_success",
            "last_bulk_price_update_failed",
            "last_bulk_price_update_total",
            "last_bulk_price_update_error",
            "last_catalog_scrape_at",
            "last_catalog_scrape_platforms",
            "last_catalog_scrape_total",
            "apscheduler_interval",
            "auto_backup_enabled",
            "auto_backup_retention",
            "last_auto_backup_at",
            "last_auto_backup_name",
            "last_auto_backup_error",
        ]
    )
    
    interval = _safe_int(meta.get("apscheduler_interval", 0), 0)
    auto_backup_enabled = str(meta.get("auto_backup_enabled", "1")).strip().lower() not in {"0", "false", "off", "no"}
    auto_backup_retention = max(1, min(_safe_int(meta.get("auto_backup_retention", 14), 14), 90))
    scheduler = {
        "scheduler_enabled": interval > 0 or auto_backup_enabled,
        "price_scheduler_enabled": interval > 0,
        "scheduler_type": "internal",
        "scheduler_cron": f"Every {interval} hours" if interval > 0 else "Off",
        "scheduler_interval": interval,
    }

    admin_status = admin_protection_status()

    def _meta_value(key, default=None):
        return meta.get(key, default)

    covered_items = max(total_items - missing_covers, 0)
    cover_coverage_pct = round((covered_items / total_items) * 100, 1) if total_items else 0.0
    providers_configured = sum(
        1
        for flag in [bool(client_id), bool(pricecharting_token), bool(ebay_client_id and ebay_client_secret), bool(rawg_key)]
        if flag
    )

    return {
        "version": APP_VERSION,
        "igdb_configured": bool(client_id),
        "pricecharting_configured": bool(pricecharting_token),
        "ebay_configured": bool(ebay_client_id and ebay_client_secret),
        "ebay_client_id_set": bool(ebay_client_id),
        "ebay_client_secret_set": bool(ebay_client_secret),
        "rawg_configured": bool(rawg_key),
        "total_items": total_items,
        "game_items": game_items,
        "non_game_items": non_game_items,
        "missing_covers": missing_covers,
        "covered_items": covered_items,
        "cover_coverage_pct": cover_coverage_pct,
        "local_covers": local_covers,
        "remote_covers": remote_covers,
        "wishlist_count": wishlist_count,
        "platforms_count": platforms_count,
        "db_size": db_size,
        "db_size_bytes": db_size_bytes,
        "uploads_files": uploads_files,
        "uploads_size": _human_size(uploads_size_bytes),
        "uploads_size_bytes": uploads_size_bytes,
        "providers_configured": providers_configured,
        "providers_total": 4,
        "last_bulk_enrich_at": _meta_value("last_bulk_enrich_at"),
        "last_bulk_enrich_success": int(_meta_value("last_bulk_enrich_success", 0) or 0),
        "last_bulk_enrich_failed": int(_meta_value("last_bulk_enrich_failed", 0) or 0),
        "last_bulk_enrich_total": int(_meta_value("last_bulk_enrich_total", 0) or 0),
        "last_bulk_price_update_at": _meta_value("last_bulk_price_update_at"),
        "last_bulk_price_update_success": int(_meta_value("last_bulk_price_update_success", 0) or 0),
        "last_bulk_price_update_failed": int(_meta_value("last_bulk_price_update_failed", 0) or 0),
        "last_bulk_price_update_total": int(_meta_value("last_bulk_price_update_total", 0) or 0),
        "last_bulk_price_update_error": _meta_value("last_bulk_price_update_error", ""),
        "last_catalog_scrape_at": _meta_value("last_catalog_scrape_at"),
        "last_catalog_scrape_platforms": _meta_value("last_catalog_scrape_platforms", ""),
        "last_catalog_scrape_total": int(_meta_value("last_catalog_scrape_total", 0) or 0),
        "auto_backup_enabled": auto_backup_enabled,
        "auto_backup_retention": auto_backup_retention,
        "auto_backup_count": len(auto_backup_files),
        "last_auto_backup_at": _meta_value("last_auto_backup_at"),
        "last_auto_backup_name": _meta_value("last_auto_backup_name", ""),
        "last_auto_backup_error": _meta_value("last_auto_backup_error", ""),
        **admin_status,
        **scheduler,
    }


@router.post("/api/settings/secrets")
async def update_secrets(payload: SecretsUpdate, _admin: None = Depends(require_admin_access)):
    updated = []
    values = {
        "igdb_client_id": payload.igdb_client_id,
        "igdb_client_secret": payload.igdb_client_secret,
        "ebay_client_id": payload.ebay_client_id,
        "ebay_client_secret": payload.ebay_client_secret,
        "rawg_api_key": payload.rawg_api_key,
        "pricecharting_token": payload.pricecharting_token,
    }

    for field, raw in values.items():
        if raw is None:
            continue
        set_app_meta(_SECRET_FIELDS[field], str(raw).strip())
        updated.append(field)

    for field in payload.clear:
        key = str(field or "").strip().lower()
        if key in _SECRET_FIELDS:
            set_app_meta(_SECRET_FIELDS[key], "")
            if key not in updated:
                updated.append(key)

    return {"ok": True, "updated": updated}

@router.post("/api/settings/scheduler")
async def update_scheduler_settings(payload: SchedulerUpdate, _admin: None = Depends(require_admin_access)):
    set_app_meta("apscheduler_interval", str(payload.interval))
    from ...scheduler import update_scheduler
    update_scheduler()
    return {"ok": True, "interval": payload.interval}


@router.post("/api/settings/auto-backup")
async def update_auto_backup_settings(payload: AutoBackupUpdate, _admin: None = Depends(require_admin_access)):
    set_app_meta("auto_backup_enabled", "1" if payload.enabled else "0")
    set_app_meta("auto_backup_retention", str(payload.retention))
    from ...scheduler import update_scheduler
    update_scheduler()
    return {"ok": True, "enabled": payload.enabled, "retention": payload.retention}

@router.post("/api/settings/clear-covers")
async def clear_all_covers(_admin: None = Depends(require_admin_access)):
    with get_db() as db:
        db.execute("UPDATE games SET cover_url = NULL")
        db.commit()
    return {"message": "All covers cleared"}


@router.delete("/api/database/clear")
async def clear_database(_admin: None = Depends(require_admin_access)):
    with get_db() as db:
        db.execute("DELETE FROM games")
        db.commit()
    return {"message": "Database cleared successfully"}
