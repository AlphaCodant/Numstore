"""
Routes API pour les portfolios.
Paiement via Paystack.
"""

import os
import uuid
import json
import logging
import httpx
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
import asyncpg

from database import get_db
from models import PortfolioSubmissionCreate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])

PAYSTACK_API_URL = "https://api.paystack.co"


def generate_reference() -> str:
    """Génère une référence unique pour la transaction."""
    return f"portfolio_{uuid.uuid4().hex[:16]}"


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
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9::jsonb, $10::jsonb, $11::jsonb, $12::jsonb, $13, $14, $15, $16, $17, $18, $19, $20, $21)""",
        submission_id, data.email, data.full_name, data.job_title, data.bio,
        data.phone, data.location, data.photo_url,
        json.dumps(data.skills), json.dumps([dict(e) for e in data.experiences]),
        json.dumps([dict(e) for e in data.education]), json.dumps([dict(p) for p in data.projects]),
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
    """Crée une session de paiement Paystack pour le portfolio."""
    
    logger.info(f"=== Payment request for submission: {submission_id} ===")
    
    submission = await db.fetchrow(
        "SELECT * FROM portfolio_submissions WHERE id = $1",
        submission_id
    )
    if not submission:
        logger.error(f"Submission not found: {submission_id}")
        raise HTTPException(status_code=404, detail="Soumission non trouvée")
    
    if submission["payment_status"] == "paid":
        raise HTTPException(status_code=400, detail="Déjà payé")
    
    product = await db.fetchrow(
        "SELECT * FROM products WHERE id = $1",
        submission["product_id"]
    )
    if not product:
        logger.error(f"Product not found: {submission['product_id']}")
        raise HTTPException(status_code=404, detail="Service non trouvé")
    
    secret_key = os.environ.get('PAYSTACK_SECRET_KEY')
    if not secret_key:
        logger.error("PAYSTACK_SECRET_KEY not configured")
        raise HTTPException(status_code=500, detail="Paystack non configuré")
    
    amount_smallest_unit = int(float(product["price"]) * 100)
    
    # Build the origin URL robustly
    origin_url = request.headers.get("origin")
    if not origin_url:
        proto = request.headers.get("x-forwarded-proto", "https")
        host = request.headers.get("x-forwarded-host") or request.headers.get("host")
        if host:
            origin_url = f"{proto}://{host}"
        else:
            origin_url = str(request.base_url).rstrip('/')
    
    reference = generate_reference()
    success_url = f"{origin_url}/portfolio/success?submission_id={submission_id}&reference={reference}"
    
    logger.info(f"Creating Paystack session: email={submission['email']}, amount={amount_smallest_unit}, ref={reference}")
    logger.info(f"Callback URL: {success_url}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{PAYSTACK_API_URL}/transaction/initialize",
                headers={
                    "Authorization": f"Bearer {secret_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "email": submission["email"],
                    "amount": amount_smallest_unit,
                    "currency": "XOF",
                    "reference": reference,
                    "callback_url": success_url,
                    "metadata": {
                        "submission_id": submission_id,
                        "product_name": product["name"],
                        "type": "portfolio",
                        "custom_fields": [
                            {"display_name": "Service", "variable_name": "service", "value": product["name"]},
                            {"display_name": "Client", "variable_name": "client", "value": submission["full_name"]}
                        ]
                    }
                }
            )
            result = response.json()
    except Exception as e:
        logger.error(f"Paystack API error: {e}")
        raise HTTPException(status_code=502, detail=f"Erreur de connexion avec Paystack: {str(e)}")
    
    logger.info(f"Paystack response: status={result.get('status')}, message={result.get('message')}")
    
    if not result.get("status"):
        raise HTTPException(status_code=400, detail=result.get("message", "Erreur Paystack"))
    
    await db.execute(
        "UPDATE portfolio_submissions SET session_id = $1 WHERE id = $2",
        reference, submission_id
    )
    
    return {
        "checkout_url": result["data"]["authorization_url"],
        "reference": reference,
        "session_id": reference
    }


@router.get("/payment-status/{submission_id}")
async def check_portfolio_payment(submission_id: str, request: Request, db: asyncpg.Connection = Depends(get_db)):
    """Vérifie le statut du paiement d'un portfolio via Paystack."""
    
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
    
    secret_key = os.environ.get('PAYSTACK_SECRET_KEY')
    if not secret_key:
        return {"status": "pending"}
    
    reference = submission["session_id"]
    
    # Vérifie via l'API Paystack
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{PAYSTACK_API_URL}/transaction/verify/{reference}",
            headers={"Authorization": f"Bearer {secret_key}"}
        )
        result = response.json()
    
    if result.get("status") and result["data"]["status"] == "success":
        await db.execute(
            "UPDATE portfolio_submissions SET payment_status = 'paid' WHERE id = $1",
            submission_id
        )
        return {"status": "paid", "message": "Paiement confirmé"}
    
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
    
    result = {key: submission[key] for key in submission.keys()}
    # Parse JSON fields
    for field in ['skills', 'experiences', 'education', 'projects']:
        if result.get(field) and isinstance(result[field], str):
            result[field] = json.loads(result[field])
    
    return result
