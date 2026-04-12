"""
NumStore - Backend FastAPI
Boutique de produits numeriques et services portfolio.
Paiement via Paystack.
"""

import os
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from database import get_pool, close_pool
from routes.pages import router as pages_router
from routes.products import router as products_router
from routes.payments import router as payments_router
from routes.access import router as access_router
from routes.portfolio import router as portfolio_router
from routes.admin import router as admin_router

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s - %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initialisation du pool PostgreSQL...")
    await get_pool()
    logger.info("Pool PostgreSQL pret.")
    yield
    logger.info("Fermeture du pool PostgreSQL...")
    await close_pool()


app = FastAPI(
    title="NumStore",
    description="Boutique de produits numeriques & Services Portfolio Premium",
    version="3.0.0",
    lifespan=lifespan,
)

# Sessions Starlette
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "numstore_secret_change_me"),
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
static_dir = ROOT_DIR / "static"
app.mount("/css", StaticFiles(directory=str(static_dir / "css")), name="css")
app.mount("/js", StaticFiles(directory=str(static_dir / "js")), name="js")
app.mount("/img", StaticFiles(directory=str(static_dir / "img")), name="img")
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Routers
app.include_router(pages_router)
app.include_router(products_router)
app.include_router(payments_router)
app.include_router(access_router)
app.include_router(portfolio_router)
app.include_router(admin_router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "app": "NumStore FastAPI v3"}


@app.get("/api")
async def api_root():
    return {"message": "NumStore API v3.0", "status": "running"}
