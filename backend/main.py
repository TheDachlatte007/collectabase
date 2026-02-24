import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Load env before importing local modules that read os.getenv at import time.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(PROJECT_ROOT / "backend" / ".env")

from .api.routes.games import router as games_router
from .api.routes.import_export import UPLOADS_DIR, router as import_export_router
from .api.routes.lookup import router as lookup_router
from .api.routes.settings import router as settings_router
from .api.routes.stats import router as stats_router
from .clz_import import router as clz_router
from .database import init_db
from .price_tracker import router as price_router

app = FastAPI(title="Collectabase", version="1.0.0")
app.include_router(games_router)
app.include_router(lookup_router)
app.include_router(import_export_router)
app.include_router(stats_router)
app.include_router(settings_router)
app.include_router(clz_router)
app.include_router(price_router)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend", "dist")
CONSOLE_FALLBACKS_DIR = os.path.join(BASE_DIR, "backend", "static", "console-fallbacks")

assets_dir = os.path.join(FRONTEND_DIR, "assets")
if os.path.isdir(assets_dir):
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

if os.path.isdir(CONSOLE_FALLBACKS_DIR):
    app.mount("/console-fallbacks", StaticFiles(directory=CONSOLE_FALLBACKS_DIR), name="console-fallbacks")

os.makedirs(UPLOADS_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")


@app.on_event("startup")
async def startup_event():
    init_db()


@app.get("/")
async def root():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.get("/{path:path}")
async def catch_all(path: str):
    if path.startswith("api/"):
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "API endpoint not found"})

    file_path = os.path.join(FRONTEND_DIR, path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
