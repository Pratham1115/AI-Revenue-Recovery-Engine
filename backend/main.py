"""
RevEngine AI — FastAPI Application Entry Point
"""
import sys
import io
# Force UTF-8 output on Windows (handles ₹ and other non-ASCII chars)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from models.database import create_tables
from routers import webhooks, dashboard, simulator

# ── App setup ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="RevEngine AI",
    description="Autonomous AI Revenue Recovery Engine — Razorpay Buildathon 2025",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow frontend (Next.js dev server on :3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── DB init ────────────────────────────────────────────────────────────────

@app.on_event("startup")
def startup():
    create_tables()
    print(f"[OK] RevEngine AI started - DB initialized")
    print(f"[DOCS] API Docs: http://localhost:8000/docs")

# ── Routers ────────────────────────────────────────────────────────────────

app.include_router(webhooks.router)
app.include_router(dashboard.router)
app.include_router(simulator.router)

# ── Health check ───────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def root():
    return {
        "service": "RevEngine AI",
        "version": settings.APP_VERSION,
        "status": "operational",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
