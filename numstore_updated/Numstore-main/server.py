"""
NumStore — Backend FastAPI (Restructuré façon gestrebFastapi)
Boutique de produits numériques et services portfolio.

Lancement :
    uvicorn server:app --host 0.0.0.0 --port 8000 --reload

Variables d'environnement requises (.env) :
    DB_HOST, DB_USER, DB_PORT, DB_PWD, DB_NAME  → PostgreSQL
    SECRET_KEY      → signature JWT admin
    STRIPE_API_KEY  → Stripe pour paiements
    RESEND_API_KEY  → Resend pour emails
    SENDER_EMAIL    → Email expéditeur
"""

import os
import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()

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

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s — %(message)s")
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
#  Lifespan : démarrage / arrêt
# ──────────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initialisation du pool PostgreSQL…")
    await get_pool()
    logger.info("✅  Pool PostgreSQL prêt.")
    yield
    logger.info("Fermeture du pool PostgreSQL…")
    await close_pool()


# ──────────────────────────────────────────────────────────────────────────────
#  Application
# ──────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="NumStore",
    description="Boutique de produits numériques & Services Portfolio Premium",
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

# ──────────────────────────────────────────────────────────────────────────────
#  Fichiers statiques
# ──────────────────────────────────────────────────────────────────────────────

app.mount("/css", StaticFiles(directory="static/css"), name="css")
app.mount("/js", StaticFiles(directory="static/js"), name="js")
app.mount("/img", StaticFiles(directory="static/img"), name="img")
app.mount("/static", StaticFiles(directory="static"), name="static")


# ──────────────────────────────────────────────────────────────────────────────
#  Routeurs
# ──────────────────────────────────────────────────────────────────────────────

app.include_router(pages_router)       # Pages templates Jinja2
app.include_router(products_router)    # /api/products
app.include_router(payments_router)    # /api/payment
app.include_router(access_router)      # /api/access
app.include_router(portfolio_router)   # /api/portfolio
app.include_router(admin_router)       # /api/admin


# ──────────────────────────────────────────────────────────────────────────────
#  Routes utilitaires
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "app": "NumStore FastAPI v3"}


@app.get("/api")
async def api_root():
    return {"message": "NumStore API v3.0", "status": "running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
