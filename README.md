# Collectabase 🕹️

A self-hosted, sleek, and automated personal game collection manager. Your free, robust alternative to CLZ Games.

![Collectabase Preview](https://via.placeholder.com/800x400.png?text=Collectabase+Preview) <!-- Add your screenshot here! -->

## ✨ Features

- **📊 Track Your Collection**: Physical games, consoles, accessories.
- **💰 Market Value Tracking**: Automated background pricing via PriceCharting and eBay.
- **🔍 Auto-Enrichment**: Instant cover art and metadata matching via IGDB & RAWG.
- **📱 Responsive Glassmorphism UI**: Beautiful, premium dark mode interface.
- **📥 Import/Export**: Easy transition from CLZ Games (CSV Import).
- **📋 Wishlist**: Track games you want and the max price you're willing to pay.
- **📈 Statistics**: Insights on your collection's value, profit/loss, and platform distribution.
- **⚡ Background Jobs**: Mass scraping and cover enrichment running silently in the background.

## 🏗️ Tech Stack

Collectabase has been completely architected for long-term stability:
- **Backend**: FastAPI + Python 3.11, SQLAlchemy (ORM), Alembic (Migrations), SQLite
- **Frontend**: Vue 3 (Composition API) + Vite, Pinia (State Management), Chart.js
- **Deployment**: Node/Nginx + Docker / Portainer

---

## 🚀 Quick Start (Docker / Portainer)

The easiest and recommended way to run Collectabase is via Docker Compose or a Portainer stack.

### 1. Setup Stack in Portainer

Create a new Stack in Portainer and use the provided `docker-compose.yml`.

Alternatively, via pure Docker:
```bash
git clone https://github.com/TheDachlatte007/collectabase.git
cd collectabase
docker-compose up -d --build
```

### 2. Available Volumes
The app stores all persistent data so you won't lose it on restarts:
- `./data:/app/data` — Contains the `games.db` SQLite database.
- `./uploads:/app/uploads` — Contains locally cached high-res cover art.

### 3. Open the App
Navigate to `http://localhost:8000` (or the port you mapped).

---

## 🔑 Configuration & API Keys

Collectabase relies on external APIs to magically enrich your collection. You don't need environment variables anymore! Everything is configured via the **Settings (Web UI)**.

1. Open the Collectabase app in your browser.
2. Go to **Settings -> Credentials**.
3. Add your keys:
   - **IGDB**: Get it from the [Twitch Dev Console](https://dev.twitch.tv/console/apps). (Used for fast cover art and metadata)
   - **RAWG**: Get it from [RAWG.io](https://rawg.io/apidocs). (Alternative metadata provider)
   - **eBay**: Get it from the [eBay Developers Program](https://developer.ebay.com/). (Used for fallback market prices)
   - **PriceCharting**: Token required for scraping/API use.
4. Click **Save Credentials**.

---

## 🛠️ Development

If you want to contribute or run the app locally for development:

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

# Run migrations to create/update tables
alembic upgrade head

# Start API
uvicorn api.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## 📝 License

MIT License. Designed with ❤️ for game collectors.
