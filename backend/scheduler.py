import asyncio
import logging
import os
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .database import get_db, get_app_meta_many
from .services.backup_service import create_automatic_backup
from .services.price.utils import PLATFORM_SLUGS, get_eur_rate
from .services.price.catalog import scrape_platform_catalog, _upsert_catalog_entries, _lookup_local_catalog_price


logger = logging.getLogger("collectabase.scheduler")

scheduler = AsyncIOScheduler()

async def scheduled_price_update():
    logger.info(f"[{datetime.now().isoformat()}] Starting scheduled_price_update")
    
    try:
        # 1. Update Catalog for owned platforms
        with get_db() as db:
            rows = db.execute("SELECT DISTINCT p.name FROM games g JOIN platforms p ON g.platform_id = p.id WHERE p.name IS NOT NULL").fetchall()
            owned_platforms = [r["name"] for r in rows]
        
        eur_rate = await get_eur_rate()
        for platform_name in owned_platforms:
            slug = PLATFORM_SLUGS.get(platform_name)
            if not slug:
                for lbl, s in PLATFORM_SLUGS.items():
                    if lbl.lower() == platform_name.lower():
                        slug = s
                        break
            if not slug:
                logger.warning(f"Could not find slug for platform {platform_name}")
                continue
                
            logger.info(f"Scraping catalog for {platform_name}...")
            entries = await scrape_platform_catalog(slug, platform_name)
            stats = _upsert_catalog_entries(entries, eur_rate)
            logger.info(f"Catalog stats for {platform_name}: {stats}")
            await asyncio.sleep(2.0)
            
        # 2. Update owned games from catalog
        with get_db() as db:
            games = db.execute("SELECT g.id, g.title, p.name as platform_name FROM games g LEFT JOIN platforms p ON g.platform_id = p.id WHERE g.is_wishlist = 0").fetchall()
            games = [dict(r) for r in games]
        
        success = 0
        for game in games:
            catalog = _lookup_local_catalog_price(game["title"], game.get("platform_name") or "")
            if not catalog:
                catalog = _lookup_local_catalog_price(game["title"], "")
                
            if catalog:
                with get_db() as db:
                    db.execute(
                        """
                        INSERT INTO price_history
                            (game_id, source, loose_price, complete_price, new_price, eur_rate, pricecharting_id)
                        VALUES (?, 'pricecharting', ?, ?, ?, 1.0, ?)
                        """,
                        (
                            game["id"],
                            catalog["loose_eur"],
                            catalog["cib_eur"],
                            catalog["new_eur"],
                            catalog["pricecharting_id"] or None,
                        ),
                    )
                    if catalog["loose_eur"] is not None:
                        db.execute("UPDATE games SET current_value = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (catalog["loose_eur"], game["id"]))
                    db.commit()
                success += 1
                
        logger.info(f"scheduled_price_update finished. Updated {success} games.")
    except Exception as e:
        logger.error(f"Error in scheduled_price_update: {e}", exc_info=True)


async def snapshot_collection_value():
    logger.info(f"[{datetime.now().isoformat()}] Starting snapshot_collection_value")
    try:
        with get_db() as db:
            total_value = db.execute("SELECT COALESCE(SUM(COALESCE(current_value, 0) * quantity), 0) FROM games WHERE is_wishlist = 0").fetchone()[0]
            game_value = db.execute("SELECT COALESCE(SUM(COALESCE(current_value, 0) * quantity), 0) FROM games WHERE is_wishlist = 0 AND item_type = 'game'").fetchone()[0]
            hardware_value = db.execute("SELECT COALESCE(SUM(COALESCE(current_value, 0) * quantity), 0) FROM games WHERE is_wishlist = 0 AND item_type != 'game'").fetchone()[0]

            db.execute(
                """
                INSERT INTO value_history (recorded_at, total_value, game_value, hardware_value)
                VALUES (CURRENT_DATE, ?, ?, ?)
                """,
                (total_value, game_value, hardware_value)
            )
            db.commit()
        logger.info(f"Successfully recorded collection snapshot: Total {total_value:.2f} (Games: {game_value:.2f}, Hardware: {hardware_value:.2f})")
    except Exception as e:
        logger.error(f"Error in snapshot_collection_value: {e}", exc_info=True)


def _auto_backup_settings() -> tuple[bool, int]:
    meta = get_app_meta_many(["auto_backup_enabled", "auto_backup_retention"])
    enabled = str(meta.get("auto_backup_enabled", "1")).strip().lower() not in {"0", "false", "off", "no"}
    try:
        retention = int(meta.get("auto_backup_retention", 14) or 14)
    except (TypeError, ValueError):
        retention = 14
    return enabled, max(1, min(retention, 90))


async def automatic_collection_backup():
    """Create a daily local recovery point without embedding provider credentials."""
    enabled, retention = _auto_backup_settings()
    if not enabled:
        return

    try:
        result = await asyncio.to_thread(create_automatic_backup, retention)
        with get_db() as db:
            db.execute(
                """
                INSERT INTO app_meta (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
                """,
                ("last_auto_backup_at", result["created_at"]),
            )
            db.execute(
                """
                INSERT INTO app_meta (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
                """,
                ("last_auto_backup_name", result["filename"]),
            )
            db.execute(
                """
                INSERT INTO app_meta (key, value, updated_at) VALUES (?, '', CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
                """,
                ("last_auto_backup_error",),
            )
            db.commit()
        logger.info("Automatic backup completed: %s", result["filename"])
    except Exception as exc:
        logger.error("Automatic backup failed: %s", exc, exc_info=True)
        with get_db() as db:
            db.execute(
                """
                INSERT INTO app_meta (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
                """,
                ("last_auto_backup_error", str(exc)[:500]),
            )
            db.commit()


def _add_snapshot_job():
    """Register the daily value-history snapshot (runs once at 03:00)."""
    scheduler.add_job(
        snapshot_collection_value,
        'cron',
        id="daily_value_snapshot",
        hour=3,
        minute=0,
        replace_existing=True,
    )
    logger.info("Daily value-history snapshot scheduled at 03:00")


def _add_auto_backup_job():
    scheduler.add_job(
        automatic_collection_backup,
        "cron",
        id="daily_collection_backup",
        hour=2,
        minute=15,
        replace_existing=True,
    )
    logger.info("Daily collection backup scheduled at 02:15")


def _remove_job(job_id: str) -> None:
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)


def _configure_scheduler() -> None:
    meta = get_app_meta_many(["apscheduler_interval"])
    try:
        interval = int(meta.get("apscheduler_interval", 0) or 0)
    except (TypeError, ValueError):
        interval = 0
    auto_backup_enabled, _retention = _auto_backup_settings()

    if interval > 0:
        scheduler.add_job(scheduled_price_update, "interval", id="price_update", hours=interval, replace_existing=True)
    else:
        _remove_job("price_update")

    if auto_backup_enabled:
        _add_auto_backup_job()
    else:
        _remove_job("daily_collection_backup")

    # Value history is useful whenever the scheduler is alive for another daily task.
    if interval > 0 or auto_backup_enabled:
        _add_snapshot_job()
        if not scheduler.running:
            scheduler.start()
        logger.info("Background scheduler configured (price interval=%s, automatic backups=%s)", interval, auto_backup_enabled)
    else:
        _remove_job("daily_value_snapshot")
        if scheduler.running:
            scheduler.shutdown(wait=False)
        logger.info("Background scheduler is disabled")


def init_scheduler():
    _configure_scheduler()

def update_scheduler():
    _configure_scheduler()

def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
    logger.info("Background scheduler shut down")
