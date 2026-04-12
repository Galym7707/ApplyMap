from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .database import Base, engine
from .routes import auth, profile, achievements, universities, reports, admin

# Create tables on startup (use Alembic migrations in production)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SourceLock API",
    description="Source-backed Common App optimization for international applicants",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(achievements.router)
app.include_router(universities.router)
app.include_router(reports.router)
app.include_router(admin.router)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "sourcelock-api"}


@app.get("/")
def root():
    return {"message": "SourceLock API", "docs": "/docs"}
