import csv
import io
import os
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from ...database import get_db

router = APIRouter()

DEFAULT_UPLOADS_DIR = "/app/uploads" if Path("/app").exists() else str(Path(__file__).resolve().parents[3] / "uploads")
UPLOADS_DIR = os.getenv("UPLOADS_DIR", DEFAULT_UPLOADS_DIR)
os.makedirs(UPLOADS_DIR, exist_ok=True)


@router.post("/api/upload/cover")
async def upload_cover(file: UploadFile = File(...)):
    import mimetypes
    import uuid

    max_size = 5 * 1024 * 1024
    allowed = {"image/jpeg", "image/png", "image/webp", "image/gif"}
    content_type = file.content_type or ""
    if content_type not in allowed:
        raise HTTPException(
            status_code=400,
            detail={"code": "bad_request", "message": "Only JPEG, PNG, WebP and GIF images are allowed."},
        )

    data = await file.read()
    if len(data) > max_size:
        raise HTTPException(
            status_code=413,
            detail={"code": "payload_too_large", "message": "File exceeds 5 MB limit."},
        )

    ext = mimetypes.guess_extension(content_type) or ".jpg"
    if ext == ".jpe":
        ext = ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOADS_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(data)
    return {"url": f"/uploads/{filename}"}


@router.post("/api/import/csv")
async def import_csv(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail={"code": "bad_request", "message": "File must be a CSV"})

    content = await file.read()
    try:
        decoded = content.decode("utf-8")
    except UnicodeDecodeError:
        decoded = content.decode("latin-1")
    reader = csv.DictReader(io.StringIO(decoded))

    def safe_float(val):
        if not val or str(val).strip() == "":
            return None
        try:
            return float(str(val).replace(",", ".").strip()) or None
        except (ValueError, TypeError):
            return None

    imported = 0
    skipped_duplicates = 0
    errors = []
    with get_db() as db:
        for row_num, row in enumerate(reader, start=2):
            try:
                platform_name = row.get("Platform", row.get("platform", "")).strip()
                if not platform_name:
                    raise ValueError("Missing platform name")
                platform_row = db.execute(
                    "SELECT id FROM platforms WHERE name = ?",
                    (platform_name,),
                ).fetchone()
                if platform_row:
                    platform_id = platform_row[0]
                else:
                    platform_type = (
                        "Console"
                        if any(
                            k in platform_name.lower()
                            for k in [
                                "playstation",
                                "xbox",
                                "nintendo",
                                "wii",
                                "gameboy",
                                "game boy",
                                "sega",
                                "dreamcast",
                                "saturn",
                                "genesis",
                                "3ds",
                                "ds",
                                "psp",
                                "vita",
                            ]
                        )
                        else "Other"
                    )
                    cursor = db.execute(
                        "INSERT INTO platforms (name, type) VALUES (?, ?)",
                        (platform_name, platform_type),
                    )
                    platform_id = cursor.lastrowid

                title_val = row.get("Title", row.get("title", "")).strip()
                if not title_val:
                    raise ValueError("Missing title")
                item_type = row.get("Type", row.get("item_type", "")).lower().strip()
                if not item_type:
                    title_lower = title_val.lower()
                    if any(
                        k in title_lower
                        for k in [
                            "gameboy",
                            "game boy",
                            "nintendo",
                            "playstation",
                            "xbox",
                            "dreamcast",
                            "console",
                            "system",
                        ]
                    ):
                        item_type = "console"
                    else:
                        item_type = "game"

                dup = db.execute(
                    "SELECT id FROM games WHERE LOWER(title) = LOWER(?) AND platform_id = ?",
                    (title_val, platform_id),
                ).fetchone()
                if dup:
                    skipped_duplicates += 1
                    continue

                db.execute(
                    """
                    INSERT INTO games (
                        title, platform_id, item_type, barcode, region, condition,
                        completeness, location, purchase_price, current_value,
                        notes, is_wishlist
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        title_val,
                        platform_id,
                        item_type,
                        row.get("Barcode", row.get("barcode")) or None,
                        row.get("Region", row.get("region")) or None,
                        row.get("Condition", row.get("condition")) or None,
                        row.get("Completeness", row.get("completeness")) or None,
                        row.get("Location", row.get("location")) or None,
                        safe_float(row.get("Purchase Price", row.get("purchase_price"))),
                        safe_float(row.get("Value", row.get("current_value"))),
                        row.get("Notes", row.get("notes", "")) or None,
                        1
                        if str(row.get("Wishlist", row.get("is_wishlist", ""))).lower()
                        in ("yes", "true", "1")
                        else 0,
                    ),
                )
                imported += 1
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
        db.commit()
    return {"imported": imported, "skipped_duplicates": skipped_duplicates, "errors": errors or None}


@router.get("/api/export/csv")
async def export_csv():
    with get_db() as db:
        cursor = db.execute(
            """
            SELECT g.title, p.name as platform, g.item_type, g.region, g.condition,
                   g.completeness, g.barcode, g.purchase_price, g.current_value,
                   g.purchase_date, g.location, g.notes, g.developer, g.publisher,
                   g.genre, g.is_wishlist
            FROM games g
            LEFT JOIN platforms p ON g.platform_id = p.id
            ORDER BY p.name, g.title
            """
        )
        rows = cursor.fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "Title",
            "Platform",
            "Type",
            "Region",
            "Condition",
            "Completeness",
            "Barcode",
            "Purchase Price",
            "Current Value",
            "Purchase Date",
            "Location",
            "Notes",
            "Developer",
            "Publisher",
            "Genre",
            "Wishlist",
        ]
    )
    for row in rows:
        writer.writerow(list(row))
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=collectabase_export.csv"},
    )

