# SourceLock

Source-backed Common App optimization tool for international applicants.

SourceLock helps students choose, rank, and rewrite their strongest honors and activities for a specific university — with source-backed guidance, not fake admission predictions.

## Tech Stack

- **Frontend**: Next.js 14 App Router + TypeScript + Tailwind CSS + shadcn/ui
- **Backend**: FastAPI (Python) + SQLAlchemy + Alembic + Pydantic
- **Database**: PostgreSQL
- **Auth**: NextAuth.js (email/password + Google)

## Getting Started

### Prerequisites

- Node.js 20+
- pnpm 8+
- Python 3.11+
- PostgreSQL 16+ (or Docker)

### Quick Start with Docker

```bash
cp .env.example .env
# Edit .env with your values
docker compose up -d
```

The app will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Development Setup

1. **Install root dependencies**
   ```bash
   pnpm install
   ```

2. **Start the database**
   ```bash
   docker compose up db -d
   ```

3. **Set up the backend**
   ```bash
   cd apps/api
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   cp ../../.env.example .env
   alembic upgrade head
   python -m src.seeds.seed_universities
   uvicorn src.main:app --reload --port 8000
   ```

4. **Set up the frontend**
   ```bash
   cd apps/web
   pnpm install
   cp ../../.env.example .env.local
   pnpm dev
   ```

## Project Structure

```
sourcelock/
├── apps/
│   ├── web/          # Next.js frontend
│   └── api/          # FastAPI backend
├── docker-compose.yml
├── turbo.json
└── pnpm-workspace.yaml
```

## Key Features

- **Achievement Vault**: Store and organize all activities and honors
- **Optimization Engine**: Weighted scoring tailored to each university's criteria
- **Rewrite Studio**: 3 style variants (factual, impact-first, understated) within Common App character limits
- **Source-Backed Guidance**: Every recommendation tied to official university sources or labeled public examples
- **Evidence Library**: Browse the sources behind each recommendation
