"""
Authentification JWT via cookie httpOnly.
Utilise PyJWT (pip install PyJWT) — pas python-jose.
"""

import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
import jwt as pyjwt

SECRET_KEY = os.getenv("SECRET_KEY", "my_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def create_access_token(data: dict) -> str:
    """Crée un token JWT signé avec expiration 1h."""
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return pyjwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """Décode un token JWT. Retourne None si invalide ou expiré."""
    try:
        return pyjwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except pyjwt.PyJWTError:
        return None


def get_current_user(request: Request) -> Optional[dict]:
    """Retourne le user depuis le cookie JWT, ou None si absent/invalide."""
    token = request.cookies.get("token")
    if not token:
        return None
    return decode_token(token)


def require_auth(request: Request) -> dict:
    """
    Dépendance FastAPI : redirige vers /connexion si non connecté.
    Usage : user = require_auth(request)
    """
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=307, headers={"Location": "/connexion"})
    return user
