# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.


This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Full stack (from repo root)
```bash
pnpm dev          # Run all apps in parallel via Turbo
pnpm build        # Build all apps
pnpm lint         # Lint all apps
pnpm type-check   # TypeScript check across all apps
```

### Frontend only (`apps/web`)
```bash
pnpm dev          # Next.js dev server on :3000
pnpm build        # Production build
pnpm lint         # ESLint
pnpm type-check   # tsc --noEmit
```

### Backend only (`apps/api`)
```bash
# Activate venv first:
source venv/bin/activate

uvicorn src.main:app --reload --port 8000   # Dev server on :8000

# Database migrations
alembic upgrade head          # Apply all migrations
alembic revision --autogenerate -m "description"  # Create new migration

# Seed data
python -m src.seeds.seed_universities   # Load university records
```

### Docker (database or full stack)
```bash
docker compose up db -d       # Start only Postgres on :5432
docker compose up -d          # Start all services (db + api + web)
```

## Architecture

### Monorepo layout
```
apps/web/    Next.js 14 App Router (TypeScript + Tailwind + shadcn/ui)
apps/api/    FastAPI (Python 3.11 + SQLAlchemy + Alembic)
```
Managed with pnpm workspaces + Turbo. No shared packages yet — each app is self-contained.

### Auth flow
The backend issues a JWT stored as both an **httpOnly cookie** (`access_token`) and **`localStorage`** (`applymap_token`, with legacy fallback for `sourcelock_token`). The FastAPI `get_current_user` dependency checks the cookie first, then the `Authorization: Bearer` header. On the frontend, `useAuth` (`apps/web/src/hooks/useAuth.ts`) wraps TanStack Query and stores the token to localStorage on login; the axios interceptor in `apps/web/src/lib/api.ts` attaches it to every request. NextAuth is a dependency but is not the primary auth mechanism — custom email/password via FastAPI is.

### API response shape
All API endpoints return `{ "data": ..., "message": "..." }`. Frontend callers access `res.data.data` to get the payload. All API functions are centralized in `apps/web/src/lib/api.ts`.

### Core domain pipeline
1. **Achievement Vault** — users store activities and honors with scoring metadata (0–10 fields: `major_relevance_score`, `selectivity_score`, `continuity_score`, `distinctiveness_score`) and categorical fields (`impact_scope`, `leadership_level`).

2. **Optimization Engine** (`apps/api/src/services/optimization_engine.py`) — runs when a report is generated. Applies `WEIGHT_PRESETS` (4 presets: `research_heavy`, `leadership_heavy`, `balanced_holistic`, `community_service_heavy`) to score each achievement. Top 10 activities / top 5 honors are recommended `keep`; duplicates get `merge`; low-description entries get `rewrite`; the rest get `remove`.

3. **Rewrite Service** (`apps/api/src/services/rewrite_service.py`) — generates 3 style variants (`factual`, `impact_first`, `understated`) for each kept/rewrite achievement, hard-truncated to Common App's 150-character activity description limit. No LLM — purely rule-based string manipulation.

4. **Report generation** runs synchronously in the route handler for MVP (see comment in `apps/api/src/routes/reports.py:166`). The `BackgroundTasks` parameter is present but the actual call is inline.

### Frontend data flow
Pages use TanStack Query with query keys like `["achievements"]`, `["reports"]`, `["targets"]`. All mutations call `queryClient.invalidateQueries` on success to keep the cache fresh. No global state store — React Query is the single source of truth for server state.

### Database models
Located in `apps/api/src/models/`. Key relationships:
- `User` → `Achievement` (one-to-many)
- `User` → `TargetUniversity` → `University` (many-to-many join)
- `User` → `OptimizationReport` → `ReportRecommendation` + `RewriteVariant` + `SourceReference`
- `University` → `UniversityPolicyEntry` (source evidence entries)

### Design system
Tailwind CSS with a custom navy color scale (`navy-50` through `navy-950`, primary brand is `navy-950 = #21278f`). All UI components are from shadcn/ui (`apps/web/src/components/ui/`). The warm off-white background (`#F9F8F6`) is used throughout. CSS variables for semantic tokens are in `apps/web/src/app/globals.css`.

### Environment variables
- Frontend needs: `NEXT_PUBLIC_API_URL`, `NEXTAUTH_URL`, `NEXTAUTH_SECRET`
- Backend needs: `DATABASE_URL`, `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `BACKEND_CORS_ORIGINS`
- Copy from `.env.example` at repo root.
