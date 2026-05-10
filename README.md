# ApplyMap

AI-powered Common App achievement optimizer for international students applying to funded universities.

ApplyMap helps students import, analyze, rank, and rewrite their activities and honors for university applications — with AI-driven scoring, automated shortlisting, and style variants that fit Common App's strict character limits.

## Tech Stack

- **Frontend**: Next.js 14 App Router + TypeScript + Tailwind CSS + shadcn/ui + TanStack Query
- **Backend**: FastAPI (Python 3.11) + SQLAlchemy + Alembic + Pydantic
- **Database**: PostgreSQL 16
- **Auth**: Custom JWT (httpOnly cookies + localStorage fallback)
- **AI**: Google Gemini API (optional, for achievement import analysis and rewrite generation)

## Getting Started

### Prerequisites

- Node.js 20+
- pnpm 8+
- Python 3.11+
- PostgreSQL 16+ (or Docker)

### Quick Start with Docker

```bash
cp .env.example .env
# Edit .env with your values (DATABASE_URL, SECRET_KEY, etc.)
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
applymap/
├── apps/
│   ├── web/          # Next.js frontend (App Router)
│   │   ├── src/app/(auth)/      # Sign-in, sign-up pages
│   │   ├── src/app/(app)/       # Protected app pages
│   │   │   ├── dashboard/       # Overview with stats and quick actions
│   │   │   ├── vault/           # Achievement management + import
│   │   │   ├── universities/    # University search and selection
│   │   │   ├── reports/         # Generated optimization reports
│   │   │   ├── advisor/         # University-specific action plans
│   │   │   ├── onboarding/      # Profile setup
│   │   │   └── evidence/        # Source library (placeholder)
│   │   ├── src/components/      # Reusable UI components
│   │   └── src/lib/api.ts       # Centralized API client
│   └── api/          # FastAPI backend
│       ├── src/models/          # SQLAlchemy models
│       ├── src/routes/          # API endpoints
│       ├── src/services/        # Business logic
│       ├── src/schemas/         # Pydantic schemas
│       └── alembic/             # Database migrations
├── docker-compose.yml
├── turbo.json
└── pnpm-workspace.yaml
```

## Implemented Features

### 1. Authentication & User Management
- **Email/password signup and login** with JWT tokens (httpOnly cookies + localStorage)
- **User profile management**: graduation year, curriculum (IB/A-Level/National), intended major, test scores (SAT/ACT/IELTS/TOEFL)
- **Onboarding flow** for new users to complete their profile
- **Protected routes** with authentication middleware

### 2. Achievement Vault (Core Feature)
- **Manual entry**: Add activities and honors with detailed fields:
  - Title, organization, role, description
  - Start/end dates, hours per week, weeks per year
  - Impact scope (school/local/regional/national/international)
  - Leadership level (none/member/lead/captain/founder)
- **Bulk import from files**: Upload PDF, DOCX, TXT, MD, CSV, or JSON files
  - AI-powered extraction using Gemini API (when configured)
  - Automatic classification into activities vs. honors
  - Fallback parsing for when AI is unavailable
  - Deduplication of imported achievements
  - Clarification questions for missing details
- **Chancellor scoring**: Automatic scoring on 4 dimensions (0-10 scale):
  - Major relevance score
  - Selectivity score
  - Continuity score
  - Distinctiveness score
- **Common App shortlist generation**: Automatically ranks top 10 activities + top 5 honors
  - Formats for Common App character limits (50/100/150 chars for activities, 100 chars for honors)
  - Generates grade levels, timing, hours/week, weeks/year
  - Identifies missing facts and verification needs
- **Drag-and-drop reordering** for activities (order persists in localStorage)
- **Status indicators**: "Strong", "Needs Detail", "Review Needed", "Analysis Pending"
- **Bulk delete** by type (all activities or all honors)

### 3. University Database & Selection
- **Pre-seeded university database** with metadata:
  - Name, country, region, application system
  - Teaching language, major strengths
  - Full-ride funding availability
  - Weight preset (research_heavy, leadership_heavy, balanced_holistic, community_service_heavy)
- **University search and filtering**:
  - By name, country, region, application system
  - By major, school years, teaching language
  - Full-ride only, Common App only filters
  - Sort by name or aid strength
- **Target university management**:
  - Add universities to your target list
  - Categorize as dream/target/safe
  - Set priority order
  - Remove from targets
- **Common App university recommendations**:
  - Based on selected top activities and honors
  - Considers user preferences (major, curriculum, graduation year)
  - Returns dream/target/safe categorization

### 4. Optimization Reports (University-Specific Analysis)
- **Generate optimization reports** for each target university:
  - Applies university-specific weight presets to score achievements
  - Top 10 activities + top 5 honors get "keep" recommendations
  - Low-scoring items get "remove" recommendations
  - Duplicates get "merge" recommendations
  - Weak descriptions get "rewrite" recommendations
- **Detailed recommendations** with:
  - Suggested rank (1-10 for activities, 1-5 for honors)
  - Recommendation type (keep/remove/rewrite/merge/reorder)
  - Rationale explaining why (based on scoring breakdown)
  - Confidence label (high/medium/low)
- **Report versioning**: Multiple reports per university tracked by version number
- **Report status tracking**: pending → processing → completed/failed
- **Export functionality**: JSON export of full report with recommendations, rewrites, and sources

### 5. Rewrite Studio (AI-Powered Text Generation)
- **3 style variants** for each kept/rewrite achievement:
  - **Factual**: Clean English preserving verified facts
  - **Impact-first** (recommended): Leads with strongest outcome/scope
  - **Understated**: Concise, restrained student voice
- **Gemini-powered generation** (when API key configured):
  - Translates Russian/Kazakh/mixed-language input to English
  - Fixes capitalization, grammar, informal phrasing
  - Preserves years, metrics, placements, event names
  - Never invents facts or inflates achievements
- **Fallback formatting** when AI unavailable:
  - Rule-based text assembly from achievement fields
  - Hard truncation to character limits
- **Format-aware limits**:
  - Common App activities: 150 characters
  - Common App honors: 100 characters
  - KAIST: 200 characters
  - Korean universities: 300 characters
- **Character count tracking** for each variant

### 6. University Advisor (Experimental)
- **Search-backed action plans** for specific universities:
  - Requires GEMINI_API_KEY or GOOGLE_SEARCH_API_KEY + GOOGLE_SEARCH_ENGINE_ID
  - Searches official university sources for admission criteria
  - Generates personalized action plan based on user's achievements
- **Action plan includes**:
  - Exams to prioritize (with priority level: high/medium/low)
  - Exact research/summer programs to target (with source URLs)
  - Profile moves that matter (concrete actions)
  - Low-value activities to avoid
  - Source notes (warnings when search unavailable)

### 7. Dashboard & Analytics
- **Profile completeness** ring chart (tracks 6 key fields)
- **Achievement counts**: Total, activities, honors
- **Activities progress bar**: Shows progress toward 10-activity Common App limit
- **Target universities count** with quick links
- **Advisors generated count** (optimization reports)
- **Recent advisors list** with status badges
- **Quick actions** based on current progress:
  - Add first achievement
  - Select target universities
  - Open new advisor
  - Manage vault
- **Contextual welcome banner** with next-step CTA

### 8. Data Models & Relationships
- **User** → **StudentProfile** (1:1)
- **User** → **Achievement** (1:many)
- **User** → **TargetUniversity** → **University** (many-to-many)
- **User** → **OptimizationReport** (1:many)
- **OptimizationReport** → **ReportRecommendation** (1:many)
- **OptimizationReport** → **RewriteVariant** (1:many)
- **OptimizationReport** → **SourceReference** (1:many)
- **University** → **UniversityPolicyEntry** (1:many)
- **Achievement** → **AchievementEvidenceFile** (1:many, file upload placeholder)

## Key Technical Details

### Backend Architecture
- **Synchronous report generation** (MVP): Reports run inline in route handler, not background tasks
- **Weight presets**: 4 predefined scoring configurations per university type
- **Duplicate detection**: Fuzzy matching on organization + title overlap
- **Scoring algorithm**: Weighted sum of 7 factors (impact, selectivity, leadership, continuity, major relevance, distinctiveness, clarity) with duplication penalty
- **Cyrillic translation**: Built-in Russian/Kazakh → English phrase mappings for common achievement terms

### Frontend Architecture
- **TanStack Query** for all server state (no Redux/Zustand)
- **Query invalidation** on mutations to keep cache fresh
- **localStorage** for:
  - Auth token (`applymap_token`, legacy `sourcelock_token`)
  - Activity drag-and-drop order (`sourcelock_activity_order`)
  - Import analysis cache (`applymap_all_import_analysis_v3`)
- **sessionStorage** for auto-shortlist signature (prevents duplicate auto-runs)
- **Axios interceptor** attaches Bearer token to all API requests
- **Custom hooks**: `useAuth` wraps user session management

### Design System
- **Navy color scale**: `navy-50` through `navy-950` (primary: `#21278f`)
- **Warm off-white background**: `#F9F8F6`
- **shadcn/ui components**: Badge, Button, Card, Dialog, Input, Select, Tabs, Textarea, etc.
- **Tailwind CSS** with custom semantic tokens in `globals.css`

## Environment Variables

### Backend (.env)
```bash
DATABASE_URL=postgresql://user:password@localhost:5432/applymap
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200
BACKEND_CORS_ORIGINS=["http://localhost:3000"]

# Optional: AI features
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.0-flash-exp

# Optional: University advisor search
GOOGLE_SEARCH_API_KEY=your-google-api-key
GOOGLE_SEARCH_ENGINE_ID=your-search-engine-id
```

### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-nextauth-secret
```

## What's NOT Implemented (Yet)

- **Google OAuth login** (NextAuth dependency present but not wired up)
- **Evidence file uploads** (model exists, S3 integration placeholder)
- **Evidence library page** (route exists, content minimal)
- **Background task processing** (BackgroundTasks imported but not used)
- **Admin panel** (route exists, functionality minimal)
- **Real-time report status updates** (polling not implemented)
- **University policy entry management** (seeded data only, no CRUD)
- **Achievement evidence verification** (truth_risk_flag set but not acted upon)
- **Multi-language UI** (English only)

## Commands Reference

See [CLAUDE.md](./CLAUDE.md) for full development commands and architecture details.
