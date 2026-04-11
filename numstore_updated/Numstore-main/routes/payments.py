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
PAYSTACK_API_URL = "https://api.paystack.co"


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
    
    # Montant en kobo (Paystack veut le montant * 100)
    amount_kobo = int(float(product["price"]) * 100)
    is_service = product["is_service"]
    reference = generate_reference()
    
    # URL de retour après paiement
    if is_service:
        callback_url = f"{data.origin_url}/portfolio/form?reference={reference}&product_id={data.product_id}&email={data.email}"
    else:
        callback_url = f"{data.origin_url}/access?reference={reference}&product_id={data.product_id}"
    
    logger.info(f"Création session Paystack: {reference}, montant: {amount_kobo}, email: {data.email}")
    
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
    
    logger.info(f"Réponse Paystack initialize: {result}")
    
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
    
    logger.info(f"Transaction créée: {transaction_id}, reference: {reference}")
    
    return {
        "checkout_url": result["data"]["authorization_url"],
        "reference": reference,
        "session_id": reference
    }


@router.get("/status/{reference}")
async def get_payment_status(
    reference: str,
    request: Request,
    db: asyncpg.Connection = Depends(get_db)
):
    """Vérifie le statut du paiement Paystack."""
    
    secret_key = os.environ.get('PAYSTACK_SECRET_KEY')
    if not secret_key:
        raise HTTPException(status_code=500, detail="Paystack non configuré")
    
    logger.info(f"=== Vérification paiement: {reference} ===")
    
    # 1. Vérifier avec l'API Paystack
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{PAYSTACK_API_URL}/transaction/verify/{reference}",
                headers={"Authorization": f"Bearer {secret_key}"}
            )
            result = response.json()
        
        logger.info(f"Paystack verify response: status={result.get('status')}, data.status={result.get('data', {}).get('status')}")
        
    except Exception as e:
        logger.error(f"Erreur appel Paystack: {e}")
        return {"status": "pending", "email_sent": False, "error": str(e)}
    
    # 2. Vérifier si le paiement est réussi
    paystack_ok = result.get("status") == True
    payment_success = result.get("data", {}).get("status") == "success"
    
    logger.info(f"paystack_ok={paystack_ok}, payment_success={payment_success}")
    
    if not (paystack_ok and payment_success):
        logger.info("Paiement pas encore confirmé par Paystack")
        return {"status": "pending", "email_sent": False}
    
    # 3. Récupérer la transaction en base
    transaction = await db.fetchrow(
        "SELECT * FROM payment_transactions WHERE session_id = $1",
        reference
    )
    
    if not transaction:
        logger.error(f"Transaction non trouvée pour reference: {reference}")
        return {"status": "error", "email_sent": False, "message": "Transaction non trouvée"}
    
    logger.info(f"Transaction trouvée: id={transaction['id']}, payment_status={transaction['payment_status']}, access_code_sent={transaction['access_code_sent']}")
    
    # 4. Si déjà traité, retourner le statut
    if transaction["payment_status"] == "paid" and transaction["access_code_sent"]:
        logger.info("Transaction déjà traitée")
        return {"status": "paid", "email_sent": True}
    
    # 5. Mettre à jour le statut en "paid"
    await db.execute(
        "UPDATE payment_transactions SET payment_status = 'paid' WHERE session_id = $1",
        reference
    )
    logger.info("Statut mis à jour: paid")
    
    # 6. Si c'est un service, pas besoin d'envoyer de code
    if transaction["is_service"]:
        await db.execute(
            "UPDATE payment_transactions SET access_code_sent = true WHERE session_id = $1",
            reference
        )
        return {"status": "paid", "is_service": True, "email_sent": True}
    
    # 7. Récupérer le produit
    product = await db.fetchrow(
        "SELECT * FROM products WHERE id = $1",
        transaction["product_id"]
    )
    
    if not product:
        logger.error(f"Produit non trouvé: {transaction['product_id']}")
        return {"status": "paid", "email_sent": False, "error": "Produit non trouvé"}
    
    # 8. Générer le code d'accès
    code = generate_access_code()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=ACCESS_CODE_VALIDITY_HOURS)
    
    logger.info(f"Code généré: {code} pour {transaction['email']}")
    
    access_code_id = str(uuid.uuid4())
    await db.execute(
        """INSERT INTO access_codes (id, code, product_id, email, order_id, created_at, expires_at, is_used)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
        access_code_id, code, transaction["product_id"],
        transaction["email"], transaction["id"],
        datetime.now(timezone.utc), expires_at, False
    )
    logger.info("Code inséré en base")
    
    # 9. Envoyer l'email
    try:
        email_sent = await send_access_code_email(
            transaction["email"], code, product["name"], ACCESS_CODE_VALIDITY_HOURS
        )
        logger.info(f"Email envoyé: {email_sent}")
    except Exception as e:
        logger.error(f"Erreur envoi email: {e}")
        email_sent = False
    
    # 10. Marquer comme traité
    await db.execute(
        "UPDATE payment_transactions SET access_code_sent = true WHERE session_id = $1",
        reference
    )
    
    return {
        "status": "paid",
        "email_sent": email_sent,
        "message": f"Code envoyé à {transaction['email']}" if email_sent else "Code généré mais email non envoyé"
    }


@router.post("/webhook")
async def paystack_webhook(request: Request, db: asyncpg.Connection = Depends(get_db)):
    """Webhook Paystack pour les événements de paiement."""
    
    secret_key = os.environ.get('PAYSTACK_SECRET_KEY')
    if not secret_key:
        logger.error("Webhook: PAYSTACK_SECRET_KEY non configuré")
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
        logger.warning("Webhook: signature invalide")
        raise HTTPException(status_code=401, detail="Signature invalide")
    
    # Parse l'événement
    event = await request.json()
    event_type = event.get("event")
    
    logger.info(f"=== Webhook Paystack reçu: {event_type} ===")
    
    if event_type == "charge.success":
        reference = event["data"]["reference"]
        logger.info(f"Webhook charge.success pour: {reference}")
        
        # Met à jour la transaction
        await db.execute(
            "UPDATE payment_transactions SET payment_status = 'paid' WHERE session_id = $1",
            reference
        )
        
        # Le reste sera géré par l'appel /status/{reference} du frontend
        logger.info(f"Transaction {reference} marquée comme paid via webhook")
        return {"status": "success"}
    
    return {"status": "ok"}
