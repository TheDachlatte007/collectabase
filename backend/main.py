from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
import httpx
import csv
import io
import os
import sqlite3
from .database import get_db, init_db, dict_from_row
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Collectabase", version="1.0.0")

# Get absolute path to frontend dist directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Go up one level to /app
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend", "dist")

# Serve frontend assets
app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()

# Pydantic Models
class IGDBSearch(BaseModel):
    title: str

class GameCreate(BaseModel):
    title: str
    platform_id: int
    item_type: Optional[str] = 'game'  # ← NEU
    barcode: Optional[str] = None
    igdb_id: Optional[int] = None
    release_date: Optional[str] = None
    publisher: Optional[str] = None
    developer: Optional[str] = None
    genre: Optional[str] = None
    description: Optional[str] = None
    cover_url: Optional[str] = None
    region: Optional[str] = None
    condition: Optional[str] = None
    completeness: Optional[str] = None
    location: Optional[str] = None
    purchase_date: Optional[str] = None
    purchase_price: Optional[float] = None
    current_value: Optional[float] = None
    notes: Optional[str] = None
    is_wishlist: bool = False
    wishlist_max_price: Optional[float] = None

class GameUpdate(GameCreate):
    pass

class PlatformCreate(BaseModel):
    name: str
    manufacturer: Optional[str] = None
    type: Optional[str] = None

# API Endpoints
@app.get("/api/games")
async def list_games(
    platform: Optional[int] = None,
    wishlist: Optional[bool] = None,
    search: Optional[str] = None
):
    """List all games with optional filters"""
    with get_db() as db:
        query = """
            SELECT g.*, p.name as platform_name 
            FROM games g
            LEFT JOIN platforms p ON g.platform_id = p.id
            WHERE 1=1
        """
        params = []
        
        if platform:
            query += " AND g.platform_id = ?"
            params.append(platform)
        
        if wishlist is not None:
            query += " AND g.is_wishlist = ?"
            params.append(1 if wishlist else 0)
        
        if search:
            query += " AND (g.title LIKE ? OR g.publisher LIKE ? OR g.developer LIKE ?)"
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param])
        
        query += " ORDER BY g.updated_at DESC"
        
        cursor = db.execute(query, params)
        games = [dict_from_row(row) for row in cursor.fetchall()]
        return games

@app.post("/api/games")
async def create_game(game: GameCreate):
    """Create a new game"""
    with get_db() as db:
        cursor = db.execute("""
            INSERT INTO games (
                title, platform_id, item_type, barcode, igdb_id, release_date,
                publisher, developer, genre, description, cover_url,
                region, condition, completeness, location,
                purchase_date, purchase_price, current_value, notes,
                is_wishlist, wishlist_max_price
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            game.title, game.platform_id, game.item_type, game.barcode, game.igdb_id, game.release_date,
            game.publisher, game.developer, game.genre, game.description, game.cover_url,
            game.region, game.condition, game.completeness, game.location,
            game.purchase_date, game.purchase_price, game.current_value, game.notes,
            1 if game.is_wishlist else 0, game.wishlist_max_price
        ))

        db.commit()
        return {"id": cursor.lastrowid, "message": "Game created successfully"}

@app.get("/api/games/{game_id}")
async def get_game(game_id: int):
    """Get a single game by ID"""
    with get_db() as db:
        cursor = db.execute("""
            SELECT g.*, p.name as platform_name 
            FROM games g
            LEFT JOIN platforms p ON g.platform_id = p.id
            WHERE g.id = ?
        """, (game_id,))
        game = dict_from_row(cursor.fetchone())
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")
        return game

@app.put("/api/games/{game_id}")
async def update_game(game_id: int, game: GameUpdate):
    """Update a game"""
    with get_db() as db:
        # Check if game exists
        existing = db.execute("SELECT id FROM games WHERE id = ?", (game_id,)).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Game not found")
        
        db.execute("""
            UPDATE games SET
                title = ?, platform_id = ?, item_type = ?, barcode = ?, igdb_id = ?, release_date = ?,
                publisher = ?, developer = ?, genre = ?, description = ?, cover_url = ?,
                region = ?, condition = ?, completeness = ?, location = ?,
                purchase_date = ?, purchase_price = ?, current_value = ?, notes = ?,
                is_wishlist = ?, wishlist_max_price = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            game.title, game.platform_id, game.item_type, game.barcode, game.igdb_id, game.release_date,
            game.publisher, game.developer, game.genre, game.description, game.cover_url,
            game.region, game.condition, game.completeness, game.location,
            game.purchase_date, game.purchase_price, game.current_value, game.notes,
            1 if game.is_wishlist else 0, game.wishlist_max_price, game_id
        ))
        db.commit()
        return {"id": game_id, "message": "Game updated successfully"}

@app.delete("/api/games/{game_id}")
async def delete_game(game_id: int):
    """Delete a game"""
    with get_db() as db:
        existing = db.execute("SELECT id FROM games WHERE id = ?", (game_id,)).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Game not found")
        
        db.execute("DELETE FROM games WHERE id = ?", (game_id,))
        db.commit()
        return {"message": "Game deleted successfully"}

# Platforms
@app.get("/api/platforms")
async def list_platforms():
    """List all platforms"""
    with get_db() as db:
        cursor = db.execute("SELECT * FROM platforms ORDER BY name")
        platforms = [dict_from_row(row) for row in cursor.fetchall()]
        return platforms

@app.post("/api/platforms")
async def create_platform(platform: PlatformCreate):
    """Create a new platform"""
    with get_db() as db:
        try:
            cursor = db.execute(
                "INSERT INTO platforms (name, manufacturer, type) VALUES (?, ?, ?)",
                (platform.name, platform.manufacturer, platform.type)
            )
            db.commit()
            return {"id": cursor.lastrowid, "message": "Platform created successfully"}
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="Platform already exists")

# IGDB Integration
@app.post("/api/lookup/igdb")
async def lookup_igdb(search:IGDBSearch):
    """Search IGDB by title"""
    title = search.title
    client_id = os.getenv("IGDB_CLIENT_ID")
    client_secret = os.getenv("IGDB_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        return {"error": "IGDB credentials not configured"}
    
    try:
        # Get access token
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://id.twitch.tv/oauth2/token",
                params={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "grant_type": "client_credentials"
                }
            )
            token_data = token_response.json()
            access_token = token_data.get("access_token")
            
            if not access_token:
                return {"error": "Failed to get IGDB access token"}
            
            # Search games
            headers = {
                "Client-ID": client_id,
                "Authorization": f"Bearer {access_token}"
            }
            
            # IGDB query
            query = f'search "{title}"; fields name,first_release_date,genres.name,platforms.name,cover.url,summary,involved_companies.company.name; limit 5;'
            
            games_response = await client.post(
                "https://api.igdb.com/v4/games",
                headers=headers,
                content=query
            )
            
            games = games_response.json()
            
            # Format results
            results = []
            for game in games:
                raw_url = game.get("cover", {}).get("url", "") if game.get("cover") else None
                # Extract developer and publisher from involved companies
                companies = game.get("involved_companies", [])
                developer = next((c["company"]["name"] for c in companies 
                                if c.get("developer") and c.get("company")), None)
                publisher = next((c["company"]["name"] for c in companies 
                                if c.get("publisher") and c.get("company")), None)
                results.append({
                    "igdb_id": game.get("id"),
                    "title": game.get("name"),
                    "release_date": game.get("first_release_date"),
                    "genre": ", ".join([g.get("name", "") for g in game.get("genres", [])]),
                    "platforms": [p.get("name", "") for p in game.get("platforms", [])],
                    "cover_url": ("https:" + raw_url.replace("t_thumb", "t_cover_big")) if raw_url else None,
                    "description": game.get("summary", ""),
                    "developer": developer,
                    "publisher": publisher,
                })
            
            return {"results": results}
    
    except Exception as e:
        return {"error": str(e)}
    

# GameTDB Platform Mapping
GAMETDB_PLATFORMS = {
    'wii': 'wii',
    'wii u': 'wiiu', 
    'gamecube': 'gc',
    'nintendo ds': 'ds',
    'nintendo 3ds': '3ds',
    'new nintendo 3ds': '3ds',
    'ps3': 'ps3',
    'playstation 3': 'ps3',
    'xbox 360': '360',
}

def get_gametdb_platform(platform_name: str) -> Optional[str]:
    """Map platform name to GameTDB platform code"""
    name_lower = platform_name.lower()
    for key, code in GAMETDB_PLATFORMS.items():
        if key in name_lower:
            return code
    return None

def extract_gametdb_id(barcode: str) -> Optional[str]:
    """Extract GameTDB game ID from barcode"""
    if not barcode:
        return None
    # Nintendo barcodes: first 4-6 chars are the game ID
    cleaned = barcode.replace('-', '').strip()
    if len(cleaned) >= 4:
        return cleaned[:6].upper()
    return None

@app.post("/api/lookup/gametdb")
async def lookup_gametdb(search: IGDBSearch):
    """Search GameTDB for cover art by title"""
    title = search.title
    
    try:
        async with httpx.AsyncClient() as client:
            # GameTDB search API
            response = await client.get(
                "https://www.gametdb.com/api.php",
                params={
                    "xml": 1,
                    "lang": "EN",
                    "name": title,
                    "region": "EN"
                },
                headers={"User-Agent": "Collectabase/1.0"}
            )
            
            if response.status_code != 200:
                return {"results": []}
            
            # Parse XML response
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.text)
            
            results = []
            for game in root.findall('.//game')[:5]:
                game_id = game.findtext('id', '')
                platform_elem = game.findtext('type', '')
                title_text = game.findtext('locale[@lang="EN"]/title') or game.findtext('title', '')
                
                # Build cover URLs
                cover_url = None
                if game_id and platform_elem:
                    cover_url = f"https://art.gametdb.com/{platform_elem}/cover/EN/{game_id}.png"
                
                results.append({
                    "source": "gametdb",
                    "gametdb_id": game_id,
                    "title": title_text,
                    "platform": platform_elem,
                    "cover_url": cover_url,
                    "cover_front": f"https://art.gametdb.com/{platform_elem}/coverfull/EN/{game_id}.png" if game_id else None,
                    "disc_art": f"https://art.gametdb.com/{platform_elem}/disc/EN/{game_id}.png" if game_id else None,
                })
            
            return {"results": results}
    
    except Exception as e:
        return {"error": str(e), "results": []}


@app.post("/api/lookup/combined")
async def lookup_combined(search: IGDBSearch):
    """Search both IGDB and GameTDB, return combined results"""
    title = search.title
    
    # Run both searches
    igdb_results = []
    gametdb_results = []
    
    # IGDB Search
    try:
        igdb_response = await lookup_igdb(search)
        igdb_results = igdb_response.get("results", [])
        for r in igdb_results:
            r["source"] = "igdb"
    except:
        pass
    
    # GameTDB Search
    try:
        gametdb_response = await lookup_gametdb(search)
        gametdb_results = gametdb_response.get("results", [])
    except:
        pass
    
    return {
        "igdb": igdb_results,
        "gametdb": gametdb_results
    }

# CSV Import
@app.post("/api/import/csv")
async def import_csv(file: UploadFile = File(...)):
    """Import games from CSV file"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    content = await file.read()
    decoded = content.decode('utf-8')
    reader = csv.DictReader(io.StringIO(decoded))
    
    imported = 0
    errors = []
    
    with get_db() as db:
        for row in reader:
            try:
                # Get or create platform
                platform_name = row.get('Platform', row.get('platform', ''))
                platform_row = db.execute(
                    "SELECT id FROM platforms WHERE name = ?",
                    (platform_name,)
                ).fetchone()
                
                if platform_row:
                    platform_id = platform_row[0]
                else:
                    # Create platform with auto-detected type
                    platform_type = "Console" if any(k in platform_name.lower() for k in [
                        'playstation', 'xbox', 'nintendo', 'wii', 'gameboy', 'game boy',
                        'sega', 'dreamcast', 'saturn', 'genesis', '3ds', 'ds', 'psp', 'vita'
                    ]) else "Other"
                    cursor = db.execute(
                        "INSERT INTO platforms (name, type) VALUES (?, ?)",
                        (platform_name, platform_type)
                    )
                    platform_id = cursor.lastrowid

                # Auto-detect item_type
                title_lower = row.get('Title', row.get('title', '')).lower()
                item_type = row.get('Type', row.get('item_type', '')).lower()
                if not item_type:
                    if any(k in title_lower for k in ['gameboy', 'game boy', 'nintendo',
                                                    'playstation', 'xbox', 'dreamcast',
                                                    'console', 'system']):
                        item_type = 'console'
                    else:
                        item_type = 'game'
                
                # Insert game
                db.execute("""
                    INSERT INTO games (
                        title, platform_id, item_type, barcode, region, condition,
                        completeness, location, purchase_price, current_value,
                        notes, is_wishlist
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row.get('Title', row.get('title', 'Unknown')),
                    platform_id,
                    item_type,
                    row.get('Barcode', row.get('barcode')),
                    row.get('Region', row.get('region')),
                    row.get('Condition', row.get('condition')),
                    row.get('Completeness', row.get('completeness')),
                    row.get('Location', row.get('location')),
                    float(row.get('Purchase Price', row.get('purchase_price', 0))) or None,
                    float(row.get('Value', row.get('current_value', 0))) or None,
                    row.get('Notes', row.get('notes', '')),
                    1 if row.get('Wishlist', row.get('is_wishlist', '')).lower() in ('yes', 'true', '1') else 0
                ))
                imported += 1
            except Exception as e:
                errors.append(f"Row {imported + len(errors) + 1}: {str(e)}")
        
        db.commit()
    
    return {
        "imported": imported,
        "errors": errors if errors else None
    }

# Statistics
@app.get("/api/stats")
async def get_stats():
    """Get collection statistics"""
    with get_db() as db:
        # Total games
        total_games = db.execute(
            "SELECT COUNT(*) FROM games WHERE is_wishlist = 0"
        ).fetchone()[0]
        
        # Total value
        total_value = db.execute(
            "SELECT COALESCE(SUM(current_value), 0) FROM games WHERE is_wishlist = 0"
        ).fetchone()[0]
        
        # Purchase value
        purchase_value = db.execute(
            "SELECT COALESCE(SUM(purchase_price), 0) FROM games WHERE is_wishlist = 0"
        ).fetchone()[0]
        
        # Wishlist count
        wishlist_count = db.execute(
            "SELECT COUNT(*) FROM games WHERE is_wishlist = 1"
        ).fetchone()[0]
        
        # Games by platform
        cursor = db.execute("""
            SELECT p.name, COUNT(*) as count, SUM(g.current_value) as value
            FROM games g
            JOIN platforms p ON g.platform_id = p.id
            WHERE g.is_wishlist = 0
            GROUP BY p.name
            ORDER BY count DESC
        """)
        by_platform = [dict_from_row(row) for row in cursor.fetchall()]
        
        # Condition distribution
        cursor = db.execute("""
            SELECT condition, COUNT(*) as count
            FROM games
            WHERE is_wishlist = 0 AND condition IS NOT NULL
            GROUP BY condition
        """)
        by_condition = [dict_from_row(row) for row in cursor.fetchall()]
        
        # By item type
        cursor = db.execute("""
            SELECT item_type, COUNT(*) as count,
                   COALESCE(SUM(current_value), 0) as value,
                   COALESCE(SUM(purchase_price), 0) as invested
            FROM games
            WHERE is_wishlist = 0
            GROUP BY item_type
            ORDER BY count DESC
        """)
        by_type = [dict_from_row(row) for row in cursor.fetchall()]


        return {
            "total_games": total_games,
            "total_value": round(total_value, 2),
            "purchase_value": round(purchase_value, 2),
            "profit_loss": round(total_value - purchase_value, 2),
            "wishlist_count": wishlist_count,
            "by_platform": by_platform,
            "by_condition": by_condition,
            "by_type": by_type
        }

# Serve frontend
@app.get("/")
async def root():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

@app.get("/{path:path}")
async def catch_all(path: str):
    """Catch-all for frontend routing"""
    if path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    
    # Check if file exists
    file_path = os.path.join(FRONTEND_DIR, path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    
    # Otherwise serve index.html for SPA routing
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
