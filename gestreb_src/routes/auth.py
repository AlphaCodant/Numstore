"""
Routes d'authentification avec rendu HTML Jinja2.
Équivalent complet des routes Express du server.js original.
"""

import secrets
import logging

import bcrypt
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from database import get_db
from auth import create_access_token, get_current_user, require_auth
from email_utils import send_email

router = APIRouter()
templates = Jinja2Templates(directory="templates")
logger = logging.getLogger(__name__)

APP_URL = "https://gestreb.net"


@router.get("/connexion", response_class=HTMLResponse)
async def page_connexion(request: Request):
    return templates.TemplateResponse("connexion.html", {
        "request": request,
        "error":   request.session.pop("error", []),
        "success": request.session.pop("success", []),
    })


@router.get("/inscription", response_class=HTMLResponse)
async def page_inscription(request: Request):
    user = get_current_user(request)
    if user:
        return RedirectResponse(f"/page/{user['tokenY']}", status_code=302)
    return templates.TemplateResponse("inscription.html", {
        "request": request,
        "error":   request.session.pop("error", []),
        "success": request.session.pop("success", []),
    })


@router.post("/connexion")
async def post_connexion(
    request: Request,
    email: str = Form(...),
    mp:    str = Form(...),
    db=Depends(get_db),
):
    user = await db.fetchrow("SELECT * FROM utilisateurs WHERE email = $1", email)
    if not user:
        request.session["error"] = ["Utilisateur non trouvé."]
        return RedirectResponse("/connexion", status_code=302)

    if not bcrypt.checkpw(mp.encode(), user["mp"].encode()):
        request.session["error"] = ["Mot de passe incorrect."]
        return RedirectResponse("/connexion", status_code=302)

    token_data = {
        "tokenY": user["token"], "email": user["email"],
        "ugf": user["ugf"], "admin": user["administrateur"],
    }
    access_token = create_access_token(token_data)

    await db.execute("UPDATE utilisateurs SET etat = 'connecte' WHERE email = $1", email)

    token_val = user["token"]
    try:
        await db.execute(f"CREATE TABLE IF NOT EXISTS parcelles_{token_val} AS (SELECT * FROM parcelles)")
        await db.execute(f"CREATE TABLE IF NOT EXISTS foret_{token_val} AS (SELECT * FROM foret)")
    except Exception as e:
        logger.warning(f"Duplication tables: {e}")

    redirect_url = f"/api/dossier/{token_val}" if user.get("statut") == "secretaire" else f"/mise_en_place/{token_val}"
    response = RedirectResponse(redirect_url, status_code=302)
    response.set_cookie("token", access_token, httponly=True, samesite="lax")
    return response


@router.post("/inscription")
async def post_inscription(
    request: Request,
    prenom: str = Form(...), nom: str = Form(...), email: str = Form(...),
    contact: str = Form(""), mat: str = Form(""), ugf: str = Form(...),
    mp: str = Form(...), rp_mp: str = Form(...),
    db=Depends(get_db),
):
    errors = []
    if not ugf:           errors.append("Vous devez choisir une UGF")
    if len(mp) < 8:       errors.append("Le mot de passe doit avoir au moins 8 caractères")
    if mp != rp_mp:       errors.append("Les mots de passe ne sont pas concordants")

    if errors:
        request.session["error"] = errors
        return RedirectResponse("/inscription", status_code=302)

    if await db.fetchrow("SELECT id FROM utilisateur WHERE email = $1", email):
        request.session["error"] = ["Cet email est déjà enregistré."]
        return RedirectResponse("/inscription", status_code=302)

    hashed = bcrypt.hashpw(mp.encode(), bcrypt.gensalt()).decode()
    token_gen = secrets.token_hex(16)

    await db.execute(
        "INSERT INTO utilisateur (prenom,nom,email,contact,matricule,ugf,mp,token,statut) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,'attente')",
        prenom, nom, email, contact, mat, ugf, hashed, token_gen,
    )

    send_email(
        to="admin@gestreb.net",
        subject=f"Demande d'accès WebSig de {nom} {prenom}",
        body=f"M.(Mme) {nom} {prenom} de matricule {mat} en service à l'UGF de {ugf} souhaite accéder à la plateforme.\nValider : {APP_URL}/valid/{token_gen}",
    )
    request.session["success"] = ["Votre inscription a été prise en compte. Vous recevrez un e-mail prochainement."]
    return RedirectResponse("/inscription", status_code=302)


@router.get("/valid/{token_gen}", response_class=HTMLResponse)
async def page_validation(request: Request, token_gen: str, db=Depends(get_db)):
    row = await db.fetchrow("SELECT * FROM utilisateur WHERE token LIKE $1", token_gen)
    if not row:
        return RedirectResponse("/connexion", status_code=302)
    return templates.TemplateResponse("validation.html", {"request": request, "tokenGen": token_gen})


@router.post("/validation/{token_gen}")
async def post_validation(request: Request, token_gen: str, db=Depends(get_db)):
    await db.execute("UPDATE utilisateur SET statut = 'valide' WHERE token LIKE $1", token_gen)
    row = await db.fetchrow("SELECT * FROM utilisateur WHERE token LIKE $1", token_gen)
    if not row:
        return RedirectResponse("/connexion", status_code=302)

    if not await db.fetchrow("SELECT id FROM utilisateurs WHERE email = $1", row["email"]):
        await db.execute(
            "INSERT INTO utilisateurs (prenom,nom,email,contact,matricule,ugf,mp,token,administrateur) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,'admin')",
            row["prenom"], row["nom"], row["email"], row["contact"], row["matricule"], row["ugf"], row["mp"], row["token"],
        )

    send_email(
        to=row["email"],
        subject="Accès accordé – Application WebSig Gestreb",
        body=f"Bonjour M./Mme {row['prenom']} {row['nom']}, votre demande a été acceptée.\nConnectez-vous sur : {APP_URL}/connexion",
    )
    return RedirectResponse("/connexion", status_code=302)


@router.post("/rejet/{token_gen}")
async def post_rejet(request: Request, token_gen: str, db=Depends(get_db)):
    await db.execute("UPDATE utilisateur SET statut = 'rejet' WHERE token LIKE $1", token_gen)
    row = await db.fetchrow("SELECT * FROM utilisateur WHERE token LIKE $1", token_gen)
    if row:
        send_email(
            to=row["email"],
            subject="Réponse à votre demande d'accès WebSig",
            body=f"Bonjour M./Mme {row['prenom']} {row['nom']}, votre demande a été rejetée. Veuillez vous rapprocher de la Direction.",
        )
    return RedirectResponse("/connexion", status_code=302)


@router.get("/log/deconnecter")
async def deconnecter(request: Request, db=Depends(get_db)):
    user = require_auth(request)
    token_y, email = user.get("tokenY"), user.get("email")

    await db.execute("UPDATE utilisateurs SET etat = 'deconnecte' WHERE email = $1", email)
    try:
        await db.execute(f"DROP TABLE IF EXISTS parcelles_{token_y}, foret_{token_y}")
    except Exception as e:
        logger.warning(f"Drop tables: {e}")

    response = RedirectResponse("/accueil", status_code=302)
    response.delete_cookie("token")
    return response
