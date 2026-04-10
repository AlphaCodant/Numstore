"""
GESTREB — Backend FastAPI
Conversion complète du server.js Express (Node.js) vers Python/FastAPI.

Lancement :
    uvicorn server:app --host 0.0.0.0 --port 3004 --reload

Variables d'environnement requises (.env) :
    DB_HOST, DB_USER, DB_PORT, DB_PWD, DB_NAME
    SECRET_KEY      → signature JWT
    MY_SECRET       → secret sessions (flash messages)
    PWD             → mot de passe SMTP
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
from routes.auth      import router as auth_router
from routes.pages     import router as pages_router
from routes.parcelles import router as parcelles_router
from routes.missions  import router as missions_router
from routes.dashboard import router as dashboard_router

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
    title="GESTREB",
    description="Gestionnaire du Reboisement — Centre de Gestion de Gagnoa",
    version="2.0.0",
    lifespan=lifespan,
)

# Sessions Starlette (équivalent express-session + express-flash)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("MY_SECRET", "mysecret_change_me"),
)

# CORS (équivalent cors({ origin: '*' }))
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────────────────────────────────────────
#  Fichiers statiques
#  Les templates référencent les assets sans préfixe :
#    /css/style.css  /js/scripts.js  /img/logo.jpg  /libs/...  /json/...
#  → on monte chaque sous-dossier à sa propre URL racine.
# ──────────────────────────────────────────────────────────────────────────────

app.mount("/css",    StaticFiles(directory="static/css"),  name="css")
app.mount("/js",     StaticFiles(directory="static/js"),   name="js")
app.mount("/img",    StaticFiles(directory="static/img"),  name="img")
app.mount("/json",   StaticFiles(directory="static/json"), name="json")
app.mount("/libs",   StaticFiles(directory="static/libs"), name="libs")
app.mount("/static", StaticFiles(directory="static"),      name="static")


# ──────────────────────────────────────────────────────────────────────────────
#  Routeurs
# ──────────────────────────────────────────────────────────────────────────────

app.include_router(pages_router)       # res.render() → TemplateResponse
app.include_router(auth_router)        # /connexion, /inscription, /valid, /rejet…
app.include_router(parcelles_router)   # /api/parcelles, /get/parcelles/*, /api/donnees…
app.include_router(missions_router)    # /mission, /api/agents, /api/planifier_mission…
app.include_router(dashboard_router)   # /dashboard/00000/:id, /requete/:id, /elements/…


# ──────────────────────────────────────────────────────────────────────────────
#  Routes utilitaires
# ──────────────────────────────────────────────────────────────────────────────

@app.post("/reinit")
async def reinit():
    return RedirectResponse("/page", status_code=302)


@app.get("/health")
async def health():
    return {"status": "ok", "app": "GESTREB FastAPI v2"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=3004, reload=True)
