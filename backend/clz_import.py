import csv
import io
from datetime import datetime
from fastapi import APIRouter, UploadFile, File
from .database import get_db

router = APIRouter()


def parse_price(price_str):
    if not price_str or str(price_str).strip() == '':
        return None
    try:
        return float(str(price_str).replace("€", "").replace(",", ".").strip()) or None
    except (ValueError, TypeError):
        return None


def parse_date(date_str):
    if not date_str or str(date_str).strip() == '':
        return None
    formats = ["%b %d, %Y", "%Y-%m-%d", "%d.%m.%Y", "%m/%d/%Y", "%Y"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
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
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    imported = 0
    skipped = 0
    errors = []

    with get_db() as db:
        # Load existing platforms for name → ID mapping
        platform_rows = db.execute("SELECT id, name FROM platforms").fetchall()
        platform_map = {row["name"].lower(): row["id"] for row in platform_rows}

        def match_platform(name):
            if not name:
                return None
            nl = name.lower().strip()
            if nl in platform_map:
                return platform_map[nl]
            for key, pid in platform_map.items():
                if nl in key or key in nl:
                    return pid
            return None

        reader = csv.DictReader(io.StringIO(text))

        for i, row in enumerate(reader, start=2):
            # Skip comment lines
            first_val = list(row.values())[0] if row else ""
            if first_val and str(first_val).startswith("#"):
                continue

            title = (row.get("title") or row.get("Title", "")).strip()
            if not title:
                skipped += 1
                continue

            platform_name = (row.get("platform_id") or row.get("Platform", "")).strip()
            pid = match_platform(platform_name)

            # Create platform if not found
            if not pid and platform_name:
                try:
                    cursor = db.execute(
                        "INSERT OR IGNORE INTO platforms (name) VALUES (?)",
                        (platform_name,)
                    )
                    pid = cursor.lastrowid
                    if not pid:
                        found = db.execute(
                            "SELECT id FROM platforms WHERE name = ?", (platform_name,)
                        ).fetchone()
                        pid = found["id"] if found else None
                    if pid:
                        platform_map[platform_name.lower()] = pid
                except Exception as e:
                    errors.append(f"Line {i}: Could not create platform '{platform_name}': {e}")

            try:
                db.execute("""
                    INSERT INTO games (
                        title, platform_id, item_type, barcode, region, condition,
                        completeness, purchase_price, current_value, purchase_date,
                        notes, genre, description, developer, publisher, release_date,
                        location, is_wishlist
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    title,
                    pid,
                    normalize_item_type(row.get("item_type") or row.get("Type", "")),
                    row.get("barcode") or row.get("Barcode") or None,
                    row.get("region") or row.get("Region") or None,
                    row.get("condition") or row.get("Condition") or None,
                    row.get("completeness") or row.get("Completeness") or None,
                    parse_price(row.get("purchase_price") or row.get("Purchase Price")),
                    parse_price(row.get("current_value") or row.get("Value")),
                    parse_date(row.get("purchase_date") or row.get("Purchase Date")),
                    row.get("notes") or row.get("Notes") or None,
                    row.get("genre") or row.get("Genre") or None,
                    row.get("description") or row.get("Description") or None,
                    row.get("developer") or row.get("Developer") or None,
                    row.get("publisher") or row.get("Publisher") or None,
                    parse_date(row.get("release_date") or row.get("Release Date")),
                    row.get("location") or row.get("Location") or None,
                    1 if str(row.get("is_wishlist", "0")).lower() in ["1", "true", "yes", "wishlist"] else 0,
                ))
                imported += 1
            except Exception as e:
                errors.append(f"Line {i}: {title} → {e}")
                skipped += 1

        db.commit()

    return {
        "imported": imported,
        "skipped": skipped,
        "errors": errors[:20]
    }
