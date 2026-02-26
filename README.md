# Collectabase 🎮

A self-hosted game collection manager — your free alternative to CLZ Games.

## Features

- 📊 Track your physical game collection
- 💰 Track purchase price & current value
- 🔍 IGDB integration for game metadata
- 📱 Responsive web interface
- 📥 Import/Export CSV
- 📋 Wishlist management
- 📈 Statistics & insights

## Quick Start

### Prerequisites

- Docker & Docker Compose
- IGDB API credentials (free from Twitch)

### 1. Clone & Setup

```bash
git clone <your-repo>
cd collectabase
cp .env.example .env
```

### 2. Get IGDB API Key

1. Go to [Twitch Developer Console](https://dev.twitch.tv/console/apps)
2. Register a new application
3. Copy Client ID and Client Secret to `.env`

### 3. Run

```bash
docker-compose up --build
```

4. Open http://localhost:8000

### Optional: Admin API Guard (recommended for remote access)

Set an admin key in your backend environment:

```bash
ADMIN_API_KEY=your-long-random-key
```

Protected admin/bulk endpoints then require `X-Admin-Key` (or `Authorization: Bearer ...`).
Without an admin key, those endpoints are only allowed from local/private clients.
If you run behind a reverse proxy and need `X-Forwarded-For`, set `TRUST_PROXY_HEADERS=true`.

## Usage

- **Add Game**: Click "+ Add Game" and fill details
- **IGDB Search**: Search by title to auto-fill metadata
- **Import CSV**: Upload exports from CLZ Games or similar
- **Track Value**: Update current values to see collection worth
- **Wishlist**: Track games you want to buy

## Tech Stack

- **Backend**: FastAPI + SQLite
- **Frontend**: Vue.js 3 + Vite
- **Deployment**: Docker

## Development

```bash
# Backend only
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend only
cd frontend
npm install
npm run dev
```

## License

MIT
