"""
Routes API pour les portfolios.
"""

import os
import uuid
import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
import asyncpg

from database import get_db
from models import PortfolioSubmissionCreate

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


@router.post("/submit")
async def submit_portfolio(data: PortfolioSubmissionCreate, db: asyncpg.Connection = Depends(get_db)):
    """Soumet les informations du portfolio (avant paiement)."""
    product = await db.fetchrow(
        "SELECT * FROM products WHERE id = $1 AND is_service = true",
        data.product_id
    )
    if not product:
        raise HTTPException(status_code=404, detail="Service non trouvé")
    
    submission_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    
    await db.execute(
        """INSERT INTO portfolio_submissions 
           (id, email, full_name, job_title, bio, phone, location, photo_url,
            skills, experiences, education, projects,
            linkedin_url, twitter_url, github_url, website_url,
            product_id, payment_status, status, created_at, updated_at)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21)""",
        submission_id, data.email, data.full_name, data.job_title, data.bio,
        data.phone, data.location, data.photo_url,
        json.dumps(data.skills), json.dumps(data.experiences),
        json.dumps(data.education), json.dumps(data.projects),
        data.linkedin_url, data.twitter_url, data.github_url, data.website_url,
        data.product_id, "pending", "pending", now, now
    )
    
    return {
        "success": True,
        "submission_id": submission_id,
        "message": "Informations enregistrées. Procédez au paiement."
    }


@router.post("/pay/{submission_id}")
async def pay_for_portfolio(submission_id: str, request: Request, db: asyncpg.Connection = Depends(get_db)):
    """Crée une session de paiement pour le portfolio."""
    from emergentintegrations.payments.stripe.checkout import (
        StripeCheckout, CheckoutSessionRequest
    )
    
    submission = await db.fetchrow(
        "SELECT * FROM portfolio_submissions WHERE id = $1",
        submission_id
    )
    if not submission:
        raise HTTPException(status_code=404, detail="Soumission non trouvée")
    
    if submission["payment_status"] == "paid":
        raise HTTPException(status_code=400, detail="Déjà payé")
    
    product = await db.fetchrow(
        "SELECT * FROM products WHERE id = $1",
        submission["product_id"]
    )
    if not product:
        raise HTTPException(status_code=404, detail="Service non trouvé")
    
    api_key = os.environ.get('STRIPE_API_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="Stripe non configuré")
    
    host_url = str(request.base_url).rstrip('/')
    webhook_url = f"{host_url}/api/payment/webhook"
    stripe_checkout = StripeCheckout(api_key=api_key, webhook_url=webhook_url)
    
    amount_usd = product["price"] / 600 if product["currency"] == "XOF" else product["price"]
    origin_url = request.headers.get("origin", host_url)
    
    success_url = f"{origin_url}/portfolio/success?submission_id={submission_id}"
    cancel_url = f"{origin_url}/portfolio/form?product_id={submission['product_id']}"
    
    checkout_request = CheckoutSessionRequest(
        amount=float(amount_usd),
        currency="usd",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "submission_id": submission_id,
            "product_name": product["name"],
            "email": submission["email"],
            "type": "portfolio"
        }
    )
    
    session = await stripe_checkout.create_checkout_session(checkout_request)
    
    await db.execute(
        "UPDATE portfolio_submissions SET session_id = $1 WHERE id = $2",
        session.session_id, submission_id
    )
    
    return {
        "checkout_url": session.url,
        "session_id": session.session_id
    }


@router.get("/payment-status/{submission_id}")
async def check_portfolio_payment(submission_id: str, request: Request, db: asyncpg.Connection = Depends(get_db)):
    """Vérifie le statut du paiement d'un portfolio."""
    from emergentintegrations.payments.stripe.checkout import StripeCheckout
    
    submission = await db.fetchrow(
        "SELECT * FROM portfolio_submissions WHERE id = $1",
        submission_id
    )
    if not submission:
        raise HTTPException(status_code=404, detail="Soumission non trouvée")
    
    if submission["payment_status"] == "paid":
        return {"status": "paid", "message": "Paiement confirmé"}
    
    if not submission["session_id"]:
        return {"status": "pending", "message": "En attente de paiement"}
    
    api_key = os.environ.get('STRIPE_API_KEY')
    if not api_key:
        return {"status": "pending"}
    
    host_url = str(request.base_url).rstrip('/')
    webhook_url = f"{host_url}/api/payment/webhook"
    stripe_checkout = StripeCheckout(api_key=api_key, webhook_url=webhook_url)
    
    try:
        status = await stripe_checkout.get_checkout_status(submission["session_id"])
        
        if status.payment_status == "paid":
            await db.execute(
                "UPDATE portfolio_submissions SET payment_status = 'paid' WHERE id = $1",
                submission_id
            )
            return {"status": "paid", "message": "Paiement confirmé"}
    except:
        pass
    
    return {"status": "pending", "message": "En attente de confirmation"}


@router.get("/submission/{submission_id}")
async def get_portfolio_submission(submission_id: str, db: asyncpg.Connection = Depends(get_db)):
    """Récupère une soumission de portfolio."""
    submission = await db.fetchrow(
        "SELECT * FROM portfolio_submissions WHERE id = $1",
        submission_id
    )
    if not submission:
        return None
    
    result = dict(submission)
    # Parse JSON fields
    for field in ['skills', 'experiences', 'education', 'projects']:
        if result.get(field) and isinstance(result[field], str):
            result[field] = json.loads(result[field])
    
    return result
