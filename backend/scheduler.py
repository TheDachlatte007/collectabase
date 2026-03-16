import asyncio
import logging
import os
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .database import get_db, get_app_meta_many
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


def init_scheduler():
    interval = int(get_app_meta_many(["apscheduler_interval"]).get("apscheduler_interval", 0))
    if interval > 0:
        scheduler.add_job(scheduled_price_update, 'interval', id="price_update", hours=interval, replace_existing=True)
        scheduler.start()
        logger.info(f"Background scheduler started with {interval} hour interval")
    else:
        logger.info("Background scheduler is disabled")

def update_scheduler():
    interval = int(get_app_meta_many(["apscheduler_interval"]).get("apscheduler_interval", 0))
    if interval > 0:
        if not scheduler.running:
            scheduler.start()
        scheduler.add_job(scheduled_price_update, 'interval', id="price_update", hours=interval, replace_existing=True)
        logger.info(f"Background scheduler updated to {interval} hour interval")
    else:
        if scheduler.get_job("price_update"):
            scheduler.remove_job("price_update")
        if scheduler.running:
            scheduler.shutdown(wait=False)

def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
    logger.info("Background scheduler shut down")
