import csv
import io
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal, Game, Platform

router = APIRouter()

def parse_price(price_str):
    if not price_str: return None
    try:
        return float(price_str.replace("€", "").replace(",", ".").strip())
    except:
        return None

def parse_date(date_str):
    if not date_str: return None
    formats = ["%b %d, %Y", "%Y-%m-%d", "%d.%m.%Y", "%m/%d/%Y", "%Y"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt).strftime("%Y-%m-%d")
        except:
            continue
    return None

def normalize_item_type(type_str):
    ts = type_str.lower().strip() if type_str else ""
    if ts in ["game", "console", "accessory", "misc"]:
        return ts
    return "game"

@router.post("/api/import/clz")
async def import_clz(file: UploadFile = File(...)):
    content = await file.read()
    try:
        text = content.decode("utf-8")
    except:
        text = content.decode("latin-1")

    db: Session = SessionLocal()
    try:
        # Plattformen laden für Name→ID Mapping
        platforms = db.query(Platform).all()
        platform_map = {p.name.lower(): p.id for p in platforms}

        def match_platform(name):
            if not name: return None
            nl = name.lower()
            for key, pid in platform_map.items():
                if nl in key or key in nl:
                    return pid
            return None

        reader = csv.DictReader(io.StringIO(text))
        imported = 0
        skipped = 0
        errors = []

        for i, row in enumerate(reader, start=2):
            # Zeilen die mit # beginnen überspringen
            if list(row.values())[0].startswith("#"):
                continue

            title = row.get("title") or row.get("Title", "").strip()
            if not title:
                skipped += 1
                continue

            platform_name = row.get("platform_id") or row.get("Platform", "")
            pid = match_platform(platform_name)

            # Plattform anlegen wenn nicht vorhanden
            if not pid and platform_name:
                new_platform = Platform(name=platform_name.strip())
                db.add(new_platform)
                db.flush()
                pid = new_platform.id
                platform_map[platform_name.lower()] = pid

            try:
                game = Game(
                    title=title,
                    platform_id=pid,
                    item_type=normalize_item_type(row.get("item_type") or row.get("Type", "")),
                    barcode=row.get("barcode") or row.get("Barcode") or None,
                    region=row.get("region") or row.get("Region") or None,
                    condition=row.get("condition") or row.get("Condition") or None,
                    completeness=row.get("completeness") or row.get("Completeness") or None,
                    purchase_price=parse_price(row.get("purchase_price") or row.get("Purchase Price")),
                    current_value=parse_price(row.get("current_value") or row.get("Value")),
                    purchase_date=parse_date(row.get("purchase_date") or row.get("Purchase Date")),
                    notes=row.get("notes") or row.get("Notes") or None,
                    is_wishlist=str(row.get("is_wishlist", "0")).lower() in ["1", "true", "yes", "wishlist"],
                    genre=row.get("genre") or row.get("Genre") or None,
                    description=row.get("description") or row.get("Description") or None,
                    developer=row.get("developer") or row.get("Developer") or None,
                    publisher=row.get("publisher") or row.get("Publisher") or None,
                    release_date=parse_date(row.get("release_date") or row.get("Release Date")),
                    location=row.get("location") or row.get("Location") or None,
                )
                db.add(game)
                imported += 1
            except Exception as e:
                errors.append(f"Zeile {i}: {title} → {str(e)}")
                skipped += 1

        db.commit()

        # Auto-enrich games without cover
        games_without_cover = db.query(Game).filter(
            Game.cover_url == None,
            Game.title != None
        ).all()

        return {
            "imported": imported,
            "skipped": skipped,
            "errors": errors[:20]  # Max 20 Fehler zurückgeben
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
