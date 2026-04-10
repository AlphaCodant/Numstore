"""
Routes API pour les paiements Paystack.
Adapté pour l'Afrique de l'Ouest (Côte d'Ivoire, XOF/CFA).
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

# Paystack API
PAYSTACK_API_URL = "https://api.paystack.co"
PAYSTACK_SECRET_KEY = os.environ.get('PAYSTACK_SECRET_KEY', '')


def generate_access_code() -> str:
    """Génère un code d'accès 6 caractères."""
    return secrets.token_hex(3).upper()


def generate_reference() -> str:
    """Génère une référence unique pour la transaction."""
    return f"numstore_{uuid.uuid4().hex[:16]}"


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
    
    secret_key = os.environ.get('PAYSTACK_SECRET_KEY')
    if not secret_key:
        raise HTTPException(status_code=500, detail="Paystack non configuré")
    
    # Montant en kobo/centimes (Paystack demande le montant en plus petite unité)
    # Pour XOF, on multiplie par 100
    amount_smallest_unit = int(float(product["price"]) * 100)
    is_service = product["is_service"]
    
    # Génère une référence unique
    reference = generate_reference()
    
    # URLs de callback
    if is_service:
        callback_url = f"{data.origin_url}/portfolio/form?reference={reference}&product_id={data.product_id}&email={data.email}"
    else:
        callback_url = f"{data.origin_url}/access?reference={reference}&product_id={data.product_id}"
    
    # Appel API Paystack
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PAYSTACK_API_URL}/transaction/initialize",
            headers={
                "Authorization": f"Bearer {secret_key}",
                "Content-Type": "application/json"
            },
            json={
                "email": data.email,
                "amount": amount_smallest_unit,
                "currency": "XOF",
                "reference": reference,
                "callback_url": callback_url,
                "metadata": {
                    "product_id": data.product_id,
                    "product_name": product["name"],
                    "is_service": str(is_service),
                    "custom_fields": [
                        {"display_name": "Produit", "variable_name": "product", "value": product["name"]}
                    ]
                }
            }
        )
        result = response.json()
    
    if not result.get("status"):
        logger.error(f"Paystack error: {result}")
        raise HTTPException(status_code=400, detail=result.get("message", "Erreur Paystack"))
    
    # Enregistre la transaction
    transaction_id = str(uuid.uuid4())
    await db.execute(
        """INSERT INTO payment_transactions 
           (id, session_id, product_id, amount, currency, email, payment_status, access_code_sent, is_service, created_at)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)""",
        transaction_id, reference, data.product_id,
        float(product["price"]), product["currency"], data.email,
        "pending", False, is_service, datetime.now(timezone.utc)
    )
    
    return {
        "checkout_url": result["data"]["authorization_url"],
        "reference": reference,
        "session_id": reference  # Pour compatibilité avec le frontend
    }


@router.get("/status/{reference}")
async def get_payment_status(
    reference: str,
    request: Request,
    db: asyncpg.Connection = Depends(get_db)
):
    """Vérifie le statut du paiement Paystack et génère le code d'accès si payé."""
    
    secret_key = os.environ.get('PAYSTACK_SECRET_KEY')
    if not secret_key:
        raise HTTPException(status_code=500, detail="Paystack non configuré")
    
    # Vérifie le paiement via l'API Paystack
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{PAYSTACK_API_URL}/transaction/verify/{reference}",
            headers={"Authorization": f"Bearer {secret_key}"}
        )
        result = response.json()
    
    if result.get("status") and result["data"]["status"] == "success":
        transaction = await db.fetchrow(
            "SELECT * FROM payment_transactions WHERE session_id = $1",
            reference
        )
        
        if transaction and not transaction["access_code_sent"]:
            product = await db.fetchrow(
                "SELECT * FROM products WHERE id = $1",
                transaction["product_id"]
            )
            
            if product:
                is_service = product["is_service"]
                
                if is_service:
                    await db.execute(
                        """UPDATE payment_transactions 
                           SET payment_status = 'paid', access_code_sent = true 
                           WHERE session_id = $1""",
                        reference
                    )
                    return {"status": "paid", "is_service": True, "message": "Paiement confirmé"}
                else:
                    # Génère le code d'accès
                    code = generate_access_code()
                    expires_at = datetime.now(timezone.utc) + timedelta(hours=ACCESS_CODE_VALIDITY_HOURS)
                    
                    access_code_id = str(uuid.uuid4())
                    await db.execute(
                        """INSERT INTO access_codes (id, code, product_id, email, order_id, created_at, expires_at, is_used)
                           VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
                        access_code_id, code, transaction["product_id"],
                        transaction["email"], transaction["id"],
                        datetime.now(timezone.utc), expires_at, False
                    )
                    
                    email_sent = await send_access_code_email(
                        transaction["email"], code, product["name"], ACCESS_CODE_VALIDITY_HOURS
                    )
                    
                    await db.execute(
                        """UPDATE payment_transactions 
                           SET payment_status = 'paid', access_code_sent = true 
                           WHERE session_id = $1""",
                        reference
                    )
                    
                    return {"status": "paid", "email_sent": email_sent, "message": f"Code envoyé à {transaction['email']}"}
        
        return {"status": "paid", "email_sent": transaction["access_code_sent"] if transaction else False}
    
    return {"status": "pending", "email_sent": False}


@router.post("/webhook")
async def paystack_webhook(request: Request, db: asyncpg.Connection = Depends(get_db)):
    """Webhook Paystack pour les événements de paiement."""
    
    secret_key = os.environ.get('PAYSTACK_SECRET_KEY')
    if not secret_key:
        return {"status": "error"}
    
    # Récupère la signature et le body
    signature = request.headers.get("x-paystack-signature", "")
    body = await request.body()
    
    # Vérifie la signature HMAC
    computed_signature = hmac.new(
        secret_key.encode('utf-8'),
        body,
        hashlib.sha512
    ).hexdigest()
    
    if not hmac.compare_digest(computed_signature, signature):
        logger.warning("Webhook Paystack: signature invalide")
        raise HTTPException(status_code=401, detail="Signature invalide")
    
    # Parse l'événement
    event = await request.json()
    event_type = event.get("event")
    
    logger.info(f"Paystack webhook reçu: {event_type}")
    
    if event_type == "charge.success":
        reference = event["data"]["reference"]
        
        # Met à jour la transaction
        await db.execute(
            "UPDATE payment_transactions SET payment_status = 'paid' WHERE session_id = $1",
            reference
        )
        
        # Génère le code d'accès si nécessaire
        transaction = await db.fetchrow(
            "SELECT * FROM payment_transactions WHERE session_id = $1",
            reference
        )
        
        if transaction and not transaction["access_code_sent"] and not transaction["is_service"]:
            product = await db.fetchrow(
                "SELECT * FROM products WHERE id = $1",
                transaction["product_id"]
            )
            
            if product:
                code = generate_access_code()
                expires_at = datetime.now(timezone.utc) + timedelta(hours=ACCESS_CODE_VALIDITY_HOURS)
                
                access_code_id = str(uuid.uuid4())
                await db.execute(
                    """INSERT INTO access_codes (id, code, product_id, email, order_id, created_at, expires_at, is_used)
                       VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
                    access_code_id, code, transaction["product_id"],
                    transaction["email"], transaction["id"],
                    datetime.now(timezone.utc), expires_at, False
                )
                
                await send_access_code_email(
                    transaction["email"], code, product["name"], ACCESS_CODE_VALIDITY_HOURS
                )
                
                await db.execute(
                    "UPDATE payment_transactions SET access_code_sent = true WHERE session_id = $1",
                    reference
                )
        
        logger.info(f"Paiement confirmé pour {reference}")
        return {"status": "success"}
    
    return {"status": "ok"}
