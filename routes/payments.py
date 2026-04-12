"""
Routes API pour les paiements Paystack.
"""

import os
import uuid
import hmac
import hashlib
import logging
import httpx
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request
import asyncpg
import secrets

from database import get_db
from models import PaymentRequest
from email_utils import send_access_code_email

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/payment", tags=["payments"])

ACCESS_CODE_VALIDITY_HOURS = 6
PAYSTACK_API_URL = "https://api.paystack.co"


def get_paystack_key():
    """Récupère la clé Paystack en nettoyant les guillemets."""
    key = os.getenv('PAYSTACK_SECRET_KEY')
    return key


def generate_access_code() -> str:
    """Génère un code d'accès 6 caractères."""
    return secrets.token_hex(3).upper()


def generate_reference() -> str:
    """Génère une référence unique."""
    return f"ns_{uuid.uuid4().hex[:12]}"


@router.post("/create-session")
async def create_payment_session(
    data: PaymentRequest,
    request: Request,
    db: asyncpg.Connection = Depends(get_db)
):
    """Crée une session de paiement Paystack."""
    
    product = await db.fetchrow(
        "SELECT * FROM products WHERE id = $1 AND is_active = true",
        data.product_id
    )
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    
    secret_key = get_paystack_key()
    if not secret_key:
        raise HTTPException(status_code=500, detail="Paystack non configuré")
    
    amount_kobo = int(float(product["price"]) * 100)
    is_service = product["is_service"]
    reference = generate_reference()
    
    # URL de retour - utilise 'reference' comme paramètre
    if is_service:
        callback_url = f"{data.origin_url}/portfolio/form?reference={reference}&product_id={data.product_id}&email={data.email}"
    else:
        callback_url = f"{data.origin_url}/access?reference={reference}&product_id={data.product_id}"
    
    logger.info(f"Création paiement: ref={reference}, email={data.email}, amount={amount_kobo}")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PAYSTACK_API_URL}/transaction/initialize",
            headers={
                "Authorization": f"Bearer {secret_key}",
                "Content-Type": "application/json"
            },
            json={
                "email": data.email,
                "amount": amount_kobo,
                "currency": "XOF",
                "reference": reference,
                "callback_url": callback_url,
                "metadata": {
                    "product_id": data.product_id,
                    "product_name": product["name"],
                    "is_service": str(is_service)
                }
            }
        )
        result = response.json()
    
    logger.info(f"Paystack response: {result.get('status')}, {result.get('message', '')}")
    
    if not result.get("status"):
        raise HTTPException(status_code=400, detail=result.get("message", "Erreur Paystack"))
    
    # Enregistre la transaction
    transaction_id = str(uuid.uuid4())
    await db.execute(
        """INSERT INTO payment_transactions 
           (id, session_id, product_id, amount, currency, email, payment_status, access_code_sent, is_service, created_at)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)""",
        transaction_id, reference, data.product_id,
        float(product["price"]), str(product["currency"]), data.email,
        "pending", False, is_service, datetime.now(timezone.utc)
    )
    
    return {
        "checkout_url": result["data"]["authorization_url"],
        "reference": reference,
        "session_id": reference
    }


@router.get("/status/{reference}")
async def get_payment_status(
    reference: str,
    db: asyncpg.Connection = Depends(get_db)
):
    """Vérifie le statut du paiement et envoie le code si payé."""
    
    secret_key = get_paystack_key()
    if not secret_key:
        raise HTTPException(status_code=500, detail="Paystack non configuré")
    
    logger.info(f"=== Vérification paiement: {reference} ===")
    
    # 1. Vérifier avec Paystack
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{PAYSTACK_API_URL}/transaction/verify/{reference}",
            headers={"Authorization": f"Bearer {secret_key}"}
        )
        result = response.json()
    
    paystack_status = result.get("data", {}).get("status", "unknown")
    logger.info(f"Paystack status: {paystack_status}")
    
    # 2. Si pas payé, retourner pending
    if paystack_status != "success":
        return {"status": "pending", "email_sent": False}
    
    # 3. Récupérer la transaction
    transaction = await db.fetchrow(
        "SELECT * FROM payment_transactions WHERE session_id = $1", reference
    )
    
    if not transaction:
        logger.error(f"Transaction non trouvée: {reference}")
        return {"status": "error", "message": "Transaction non trouvée"}
    
    logger.info(f"Transaction: status={transaction['payment_status']}, code_sent={transaction['access_code_sent']}")
    
    # 4. Si déjà traité, retourner success
    if transaction["access_code_sent"]:
        return {"status": "paid", "email_sent": True}
    
    # 5. Mettre à jour le statut
    await db.execute(
        "UPDATE payment_transactions SET payment_status = 'paid' WHERE id = $1",
        transaction["id"]
    )
    logger.info("Statut mis à jour: paid")
    
    # 6. Si c'est un service, pas de code à envoyer
    if transaction["is_service"]:
        await db.execute(
            "UPDATE payment_transactions SET access_code_sent = true WHERE id = $1",
            transaction["id"]
        )
        return {"status": "paid", "is_service": True, "email_sent": True}
    
    # 7. Récupérer le produit
    product = await db.fetchrow(
        "SELECT * FROM products WHERE id = $1", transaction["product_id"]
    )
    
    if not product:
        return {"status": "paid", "email_sent": False, "error": "Produit non trouvé"}
    
    # 8. Générer et sauvegarder le code
    code = generate_access_code()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=ACCESS_CODE_VALIDITY_HOURS)
    
    logger.info(f"Code généré: {code} pour {transaction['email']}")
    
    await db.execute(
        """INSERT INTO access_codes (id, code, product_id, email, order_id, created_at, expires_at, is_used)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
        str(uuid.uuid4()), code, transaction["product_id"],
        transaction["email"], transaction["id"],
        datetime.now(timezone.utc), expires_at, False
    )
    
    # 9. Envoyer l'email
    email_sent = await send_access_code_email(
        transaction["email"], code, product["name"], ACCESS_CODE_VALIDITY_HOURS
    )
    logger.info(f"Email envoyé: {email_sent}")
    
    # 10. Marquer comme traité
    await db.execute(
        "UPDATE payment_transactions SET access_code_sent = true WHERE id = $1",
        transaction["id"]
    )
    
    return {"status": "paid", "email_sent": email_sent}


@router.post("/webhook")
async def paystack_webhook(request: Request, db: asyncpg.Connection = Depends(get_db)):
    """Webhook Paystack."""
    
    secret_key = get_paystack_key()
    if not secret_key:
        return {"status": "error"}
    
    signature = request.headers.get("x-paystack-signature", "")
    body = await request.body()
    
    computed = hmac.new(secret_key.encode(), body, hashlib.sha512).hexdigest()
    
    if not hmac.compare_digest(computed, signature):
        logger.warning("Webhook: signature invalide")
        raise HTTPException(status_code=401, detail="Signature invalide")
    
    event = await request.json()
    event_type = event.get("event")
    
    logger.info(f"Webhook reçu: {event_type}")
    
    if event_type == "charge.success":
        reference = event["data"]["reference"]
        await db.execute(
            "UPDATE payment_transactions SET payment_status = 'paid' WHERE session_id = $1",
            reference
        )
        logger.info(f"Transaction {reference} marquée paid via webhook")
    
    return {"status": "ok"}
