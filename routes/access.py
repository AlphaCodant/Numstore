"""
Routes API pour les codes d'acces.
"""

import os
import uuid
import secrets
import logging
from pathlib import Path
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
import asyncpg

from database import get_db
from models import AccessRequest, ResendCodeRequest
from email_utils import send_access_code_email

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/access", tags=["access"])

ACCESS_CODE_VALIDITY_HOURS = 6
UPLOADS_DIR = Path(__file__).parent.parent / "uploads"


def generate_access_code() -> str:
    """Génère un code d'accès 6 caractères."""
    return secrets.token_hex(3).upper()


@router.post("/verify")
async def verify_access_code(data: AccessRequest, db: asyncpg.Connection = Depends(get_db)):
    """Vérifie un code d'accès et retourne les infos du produit."""
    access_code = await db.fetchrow(
        "SELECT * FROM access_codes WHERE code = $1",
        data.code.upper()
    )
    
    if not access_code:
        raise HTTPException(status_code=404, detail="Code invalide")
    
    # Vérifie l'expiration
    expires_at = access_code["expires_at"]
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    
    if datetime.now(timezone.utc) > expires_at:
        raise HTTPException(
            status_code=410, 
            detail="Code expiré. Cliquez sur 'Renvoyer le code' pour en recevoir un nouveau."
        )
    
    product = await db.fetchrow(
        "SELECT * FROM products WHERE id = $1",
        access_code["product_id"]
    )
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    
    # Calcule le temps restant
    remaining_seconds = (expires_at - datetime.now(timezone.utc)).total_seconds()
    remaining_hours = int(remaining_seconds // 3600)
    remaining_minutes = int((remaining_seconds % 3600) // 60)
    
    # Build download URL - use secure endpoint
    has_local_file = product["download_url"] and product["download_url"].startswith("/api/admin/files/")
    if has_local_file:
        download_url = f"/api/access/download/{product['id']}?code={data.code.upper()}"
    else:
        download_url = product["download_url"] or ""
    
    return {
        "valid": True,
        "product": {
            "id": product["id"],
            "name": product["name"],
            "description": product["description"],
            "download_url": download_url,
            "file_size": product["file_size"],
            "has_local_file": has_local_file
        },
        "expires_in": f"{remaining_hours}h {remaining_minutes}min",
        "expires_at": expires_at.isoformat()
    }


@router.post("/resend")
async def resend_access_code(data: ResendCodeRequest, db: asyncpg.Connection = Depends(get_db)):
    """Renvoie un nouveau code d'accès."""
    # Cherche une transaction payée pour cet email
    if data.product_id:
        transaction = await db.fetchrow(
            """SELECT * FROM payment_transactions 
               WHERE email = $1 AND payment_status = 'paid' AND is_service = false AND product_id = $2
               ORDER BY created_at DESC LIMIT 1""",
            data.email, data.product_id
        )
    else:
        transaction = await db.fetchrow(
            """SELECT * FROM payment_transactions 
               WHERE email = $1 AND payment_status = 'paid' AND is_service = false
               ORDER BY created_at DESC LIMIT 1""",
            data.email
        )
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Aucun achat trouvé pour cet email")
    
    product = await db.fetchrow(
        "SELECT * FROM products WHERE id = $1",
        transaction["product_id"]
    )
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    
    # Génère un nouveau code
    code = generate_access_code()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=ACCESS_CODE_VALIDITY_HOURS)
    
    access_code_id = str(uuid.uuid4())
    await db.execute(
        """INSERT INTO access_codes (id, code, product_id, email, order_id, created_at, expires_at, is_used)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
        access_code_id, code, transaction["product_id"],
        data.email, transaction["id"],
        datetime.now(timezone.utc), expires_at, False
    )
    
    email_sent = await send_access_code_email(data.email, code, product["name"], ACCESS_CODE_VALIDITY_HOURS)
    
    if not email_sent:
        raise HTTPException(status_code=500, detail="Erreur lors de l'envoi de l'email")
    
    return {"success": True, "message": f"Nouveau code envoyé à {data.email}", "product_name": product["name"]}



@router.get("/download/{product_id}")
async def download_product_file(product_id: str, code: str, db: asyncpg.Connection = Depends(get_db)):
    """Telecharge un fichier produit apres verification du code d'acces."""
    
    # Verify access code
    access_code = await db.fetchrow(
        "SELECT * FROM access_codes WHERE code = $1 AND product_id = $2",
        code.upper(), product_id
    )
    
    if not access_code:
        raise HTTPException(status_code=403, detail="Code d'acces invalide")
    
    # Check expiration
    expires_at = access_code["expires_at"]
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    
    if datetime.now(timezone.utc) > expires_at:
        raise HTTPException(status_code=410, detail="Code expire")
    
    # Get product
    product = await db.fetchrow("SELECT * FROM products WHERE id = $1", product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouve")
    
    download_url = product["download_url"]
    if not download_url or not download_url.startswith("/api/admin/files/"):
        raise HTTPException(status_code=404, detail="Aucun fichier disponible pour ce produit")
    
    # Extract filename and serve file
    filename = download_url.split("/")[-1]
    filepath = UPLOADS_DIR / filename
    
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Fichier non trouve sur le serveur")
    
    # Use original product name as download filename
    ext = Path(filename).suffix
    safe_name = product["name"].replace(" ", "_").replace("/", "-") + ext
    
    logger.info(f"Download: {safe_name} by code {code}")
    
    return FileResponse(
        filepath,
        filename=safe_name,
        media_type="application/octet-stream"
    )
