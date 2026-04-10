"""
Routes API pour les paiements Stripe.
"""

import os
import uuid
import logging
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


def generate_access_code() -> str:
    """Génère un code d'accès 6 caractères."""
    return secrets.token_hex(3).upper()


@router.post("/create-session")
async def create_payment_session(
    data: PaymentRequest,
    request: Request,
    db: asyncpg.Connection = Depends(get_db)
):
    """Crée une session de paiement Stripe."""
    from emergentintegrations.payments.stripe.checkout import (
        StripeCheckout, CheckoutSessionRequest
    )
    
    product = await db.fetchrow(
        "SELECT * FROM products WHERE id = $1 AND is_active = true",
        data.product_id
    )
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    
    api_key = os.environ.get('STRIPE_API_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="Stripe non configuré")
    
    host_url = str(request.base_url).rstrip('/')
    webhook_url = f"{host_url}/api/payment/webhook"
    stripe_checkout = StripeCheckout(api_key=api_key, webhook_url=webhook_url)
    
    # Conversion XOF -> USD (1 USD ≈ 600 XOF)
    amount_usd = product["price"] / 600 if product["currency"] == "XOF" else product["price"]
    is_service = product["is_service"]
    
    if is_service:
        success_url = f"{data.origin_url}/portfolio/form?order_id={{CHECKOUT_SESSION_ID}}&product_id={data.product_id}&email={data.email}"
    else:
        success_url = f"{data.origin_url}/access?session_id={{CHECKOUT_SESSION_ID}}&product_id={data.product_id}"
    
    cancel_url = f"{data.origin_url}/product/{data.product_id}"
    
    checkout_request = CheckoutSessionRequest(
        amount=float(amount_usd),
        currency="usd",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "product_id": data.product_id,
            "product_name": product["name"],
            "email": data.email,
            "is_service": str(is_service)
        }
    )
    
    session = await stripe_checkout.create_checkout_session(checkout_request)
    
    # Enregistre la transaction
    transaction_id = str(uuid.uuid4())
    await db.execute(
        """INSERT INTO payment_transactions 
           (id, session_id, product_id, amount, currency, email, payment_status, access_code_sent, is_service, created_at)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)""",
        transaction_id, session.session_id, data.product_id,
        product["price"], product["currency"], data.email,
        "pending", False, is_service, datetime.now(timezone.utc)
    )
    
    return {
        "checkout_url": session.url,
        "session_id": session.session_id
    }


@router.get("/status/{session_id}")
async def get_payment_status(
    session_id: str,
    request: Request,
    db: asyncpg.Connection = Depends(get_db)
):
    """Vérifie le statut du paiement et génère le code d'accès si payé."""
    from emergentintegrations.payments.stripe.checkout import StripeCheckout
    
    api_key = os.environ.get('STRIPE_API_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="Stripe non configuré")
    
    host_url = str(request.base_url).rstrip('/')
    webhook_url = f"{host_url}/api/payment/webhook"
    stripe_checkout = StripeCheckout(api_key=api_key, webhook_url=webhook_url)
    
    status = await stripe_checkout.get_checkout_status(session_id)
    
    if status.payment_status == "paid":
        transaction = await db.fetchrow(
            "SELECT * FROM payment_transactions WHERE session_id = $1",
            session_id
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
                        session_id
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
                        session_id
                    )
                    
                    return {"status": "paid", "email_sent": email_sent, "message": f"Code envoyé à {transaction['email']}"}
        
        return {"status": "paid", "email_sent": transaction["access_code_sent"] if transaction else False}
    
    return {"status": status.payment_status, "email_sent": False}


@router.post("/webhook")
async def stripe_webhook(request: Request, db: asyncpg.Connection = Depends(get_db)):
    """Webhook Stripe pour les événements de paiement."""
    from emergentintegrations.payments.stripe.checkout import StripeCheckout
    
    body = await request.body()
    signature = request.headers.get("Stripe-Signature")
    api_key = os.environ.get('STRIPE_API_KEY')
    
    if not api_key:
        return {"status": "error"}
    
    host_url = str(request.base_url).rstrip('/')
    webhook_url = f"{host_url}/api/payment/webhook"
    stripe_checkout = StripeCheckout(api_key=api_key, webhook_url=webhook_url)
    
    try:
        webhook_response = await stripe_checkout.handle_webhook(body, signature)
        if webhook_response.payment_status == "paid":
            await db.execute(
                "UPDATE payment_transactions SET payment_status = 'paid' WHERE session_id = $1",
                webhook_response.session_id
            )
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error"}
