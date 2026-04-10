from fastapi import FastAPI, APIRouter, HTTPException, Request
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import asyncio
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict
import uuid
from datetime import datetime, timezone, timedelta
import secrets
import resend
from emergentintegrations.payments.stripe.checkout import (
    StripeCheckout, CheckoutSessionRequest
)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Resend configuration
RESEND_API_KEY = os.environ.get('RESEND_API_KEY')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'onboarding@resend.dev')
if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY

# Access code validity (6 hours)
ACCESS_CODE_VALIDITY_HOURS = 6

# Create the main app
app = FastAPI(title="NumStore API", version="2.1.0")
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== MODELS ====================

class Product(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    price: float
    currency: str = "XOF"  # FCFA
    category: str
    image_url: Optional[str] = None
    download_url: Optional[str] = None
    file_size: Optional[str] = None
    is_service: bool = False  # True for portfolio service
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_active: bool = True

class ProductCreate(BaseModel):
    name: str
    description: str
    price: float
    currency: str = "XOF"
    category: str
    image_url: Optional[str] = None
    download_url: Optional[str] = None
    file_size: Optional[str] = None
    is_service: bool = False

class AccessCode(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str
    product_id: str
    email: str
    order_id: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    expires_at: str
    is_used: bool = False

class PaymentTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    product_id: str
    amount: float
    currency: str = "XOF"
    email: str
    payment_status: str = "pending"
    access_code_sent: bool = False
    is_service: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class PaymentRequest(BaseModel):
    product_id: str
    email: EmailStr
    origin_url: str

class AccessRequest(BaseModel):
    code: str

class ResendCodeRequest(BaseModel):
    email: EmailStr
    product_id: Optional[str] = None

# Portfolio Models
class PortfolioSubmission(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    # Personal Info
    full_name: str
    job_title: str
    bio: str
    phone: Optional[str] = None
    location: Optional[str] = None
    photo_url: Optional[str] = None
    # Professional Info
    skills: List[str] = []
    experiences: List[Dict] = []  # {company, role, duration, description}
    education: List[Dict] = []    # {school, degree, year}
    projects: List[Dict] = []     # {title, description, image_url, link}
    # Social Links
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    github_url: Optional[str] = None
    website_url: Optional[str] = None
    # Product & Payment
    product_id: str
    payment_status: str = "pending"  # pending, paid
    session_id: Optional[str] = None
    # Status
    status: str = "pending"  # pending, in_progress, completed
    portfolio_url: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class PortfolioSubmissionCreate(BaseModel):
    email: str
    full_name: str
    job_title: str
    bio: str
    phone: Optional[str] = None
    location: Optional[str] = None
    photo_url: Optional[str] = None
    skills: List[str] = []
    experiences: List[Dict] = []
    education: List[Dict] = []
    projects: List[Dict] = []
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    github_url: Optional[str] = None
    website_url: Optional[str] = None
    product_id: str

# ==================== HELPERS ====================

def generate_access_code():
    """Generate a 6-character alphanumeric access code"""
    return secrets.token_hex(3).upper()

def format_price(amount: float, currency: str = "XOF") -> str:
    """Format price with currency"""
    if currency == "XOF":
        return f"{int(amount):,} FCFA".replace(",", " ")
    return f"${amount:.2f}"

async def send_access_code_email(email: str, code: str, product_name: str, expires_in_hours: int = 6):
    """Send access code via Resend"""
    if not RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not configured, skipping email")
        return False
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
        <div style="background-color: #ffffff; padding: 40px; border-radius: 8px;">
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #0055FF; margin: 0; font-size: 28px;">NumStore</h1>
            </div>
            <h2 style="color: #0a0a0a; margin-bottom: 20px;">Votre code d'accès</h2>
            <p style="color: #52525b; font-size: 16px; line-height: 1.6;">
                Merci pour votre achat de <strong>{product_name}</strong> !
            </p>
            <div style="background-color: #f4f4f5; padding: 30px; text-align: center; margin: 30px 0; border-radius: 8px;">
                <p style="color: #52525b; margin: 0 0 10px 0; font-size: 14px;">Votre code d'accès :</p>
                <h1 style="color: #0055FF; font-size: 42px; letter-spacing: 8px; margin: 0; font-family: monospace;">{code}</h1>
            </div>
            <p style="color: #52525b; font-size: 14px; line-height: 1.6;">
                ⏰ <strong>Ce code est valide pendant {expires_in_hours} heures.</strong>
            </p>
        </div>
    </body>
    </html>
    """
    
    try:
        params = {"from": SENDER_EMAIL, "to": [email], "subject": f"🔐 Votre code d'accès NumStore - {product_name}", "html": html_content}
        result = await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"Email sent to {email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False

async def send_portfolio_form_email(email: str, order_id: str, product_name: str, form_url: str):
    """Send portfolio form link via email"""
    if not RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not configured, skipping email")
        return False
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
        <div style="background-color: #ffffff; padding: 40px; border-radius: 8px;">
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #0055FF; margin: 0; font-size: 28px;">NumStore</h1>
            </div>
            <h2 style="color: #0a0a0a; margin-bottom: 20px;">🎉 Bienvenue !</h2>
            <p style="color: #52525b; font-size: 16px; line-height: 1.6;">
                Merci pour votre achat de <strong>{product_name}</strong> !
            </p>
            <p style="color: #52525b; font-size: 16px; line-height: 1.6;">
                Pour créer votre portfolio professionnel, veuillez remplir le formulaire ci-dessous avec vos informations :
            </p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{form_url}" style="display: inline-block; background-color: #0055FF; color: white; padding: 16px 32px; text-decoration: none; font-weight: bold; border-radius: 4px;">
                    Remplir mon formulaire
                </a>
            </div>
            <p style="color: #52525b; font-size: 14px; line-height: 1.6;">
                Une fois le formulaire complété, notre équipe créera votre portfolio personnalisé et vous recevrez le lien par email.
            </p>
            <hr style="border: none; border-top: 1px solid #e4e4e7; margin: 30px 0;">
            <p style="color: #a1a1aa; font-size: 12px; text-align: center;">
                NumStore - Produits Numériques & Services Premium
            </p>
        </div>
    </body>
    </html>
    """
    
    try:
        params = {"from": SENDER_EMAIL, "to": [email], "subject": f"📋 Créez votre portfolio - {product_name}", "html": html_content}
        result = await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"Portfolio form email sent to {email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False

# ==================== PRODUCT ROUTES ====================

@api_router.get("/products", response_model=List[Product])
async def get_products(category: Optional[str] = None):
    query = {"is_active": True}
    if category:
        query["category"] = category
    products = await db.products.find(query, {"_id": 0}).to_list(1000)
    return products

@api_router.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: str):
    product = await db.products.find_one({"id": product_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    return product

# ==================== PAYMENT ROUTES ====================

@api_router.post("/payment/create-session")
async def create_payment_session(data: PaymentRequest, request: Request):
    """Create Stripe payment session for a product"""
    product = await db.products.find_one({"id": data.product_id, "is_active": True}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    
    api_key = os.environ.get('STRIPE_API_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="Stripe non configuré")
    
    host_url = str(request.base_url).rstrip('/')
    webhook_url = f"{host_url}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=api_key, webhook_url=webhook_url)
    
    # Convert XOF to USD for Stripe (approximate rate: 1 USD = 600 XOF)
    amount_usd = product["price"] / 600 if product.get("currency") == "XOF" else product["price"]
    
    is_service = product.get("is_service", False)
    
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
    
    # Create payment transaction record
    transaction = PaymentTransaction(
        session_id=session.session_id,
        product_id=data.product_id,
        amount=product["price"],
        currency=product.get("currency", "XOF"),
        email=data.email,
        payment_status="pending",
        is_service=is_service
    )
    await db.payment_transactions.insert_one(transaction.model_dump())
    
    return {
        "checkout_url": session.url,
        "session_id": session.session_id
    }

@api_router.get("/payment/status/{session_id}")
async def get_payment_status(session_id: str, request: Request):
    """Check payment status and handle accordingly"""
    api_key = os.environ.get('STRIPE_API_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="Stripe non configuré")
    
    host_url = str(request.base_url).rstrip('/')
    webhook_url = f"{host_url}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=api_key, webhook_url=webhook_url)
    
    status = await stripe_checkout.get_checkout_status(session_id)
    
    if status.payment_status == "paid":
        transaction = await db.payment_transactions.find_one({"session_id": session_id}, {"_id": 0})
        
        if transaction and not transaction.get("access_code_sent"):
            product = await db.products.find_one({"id": transaction["product_id"]}, {"_id": 0})
            
            if product:
                is_service = product.get("is_service", False)
                
                if is_service:
                    # For services, just mark as paid
                    await db.payment_transactions.update_one(
                        {"session_id": session_id},
                        {"$set": {"payment_status": "paid", "access_code_sent": True}}
                    )
                    return {"status": "paid", "is_service": True, "message": "Paiement confirmé"}
                else:
                    # For products, generate access code
                    code = generate_access_code()
                    expires_at = (datetime.now(timezone.utc) + timedelta(hours=ACCESS_CODE_VALIDITY_HOURS)).isoformat()
                    
                    access_code = AccessCode(
                        code=code,
                        product_id=transaction["product_id"],
                        email=transaction["email"],
                        order_id=transaction["id"],
                        expires_at=expires_at
                    )
                    await db.access_codes.insert_one(access_code.model_dump())
                    
                    email_sent = await send_access_code_email(
                        transaction["email"], code, product["name"], ACCESS_CODE_VALIDITY_HOURS
                    )
                    
                    await db.payment_transactions.update_one(
                        {"session_id": session_id},
                        {"$set": {"payment_status": "paid", "access_code_sent": True}}
                    )
                    
                    return {"status": "paid", "email_sent": email_sent, "message": f"Code envoyé à {transaction['email']}"}
        
        return {"status": "paid", "email_sent": transaction.get("access_code_sent", False) if transaction else False}
    
    return {"status": status.payment_status, "email_sent": False}

@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("Stripe-Signature")
    api_key = os.environ.get('STRIPE_API_KEY')
    if not api_key:
        return {"status": "error"}
    
    host_url = str(request.base_url).rstrip('/')
    webhook_url = f"{host_url}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=api_key, webhook_url=webhook_url)
    
    try:
        webhook_response = await stripe_checkout.handle_webhook(body, signature)
        if webhook_response.payment_status == "paid":
            await db.payment_transactions.update_one(
                {"session_id": webhook_response.session_id},
                {"$set": {"payment_status": "paid"}}
            )
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error"}

# ==================== ACCESS CODE ROUTES ====================

@api_router.post("/access/verify")
async def verify_access_code(data: AccessRequest):
    access_code = await db.access_codes.find_one({"code": data.code.upper()}, {"_id": 0})
    
    if not access_code:
        raise HTTPException(status_code=404, detail="Code invalide")
    
    expires_at = datetime.fromisoformat(access_code["expires_at"].replace('Z', '+00:00'))
    if datetime.now(timezone.utc) > expires_at:
        raise HTTPException(status_code=410, detail="Code expiré. Cliquez sur 'Renvoyer le code' pour en recevoir un nouveau.")
    
    product = await db.products.find_one({"id": access_code["product_id"]}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    
    remaining_seconds = (expires_at - datetime.now(timezone.utc)).total_seconds()
    remaining_hours = int(remaining_seconds // 3600)
    remaining_minutes = int((remaining_seconds % 3600) // 60)
    
    return {
        "valid": True,
        "product": {
            "id": product["id"],
            "name": product["name"],
            "description": product["description"],
            "download_url": product.get("download_url", "https://example.com/download"),
            "file_size": product.get("file_size")
        },
        "expires_in": f"{remaining_hours}h {remaining_minutes}min",
        "expires_at": access_code["expires_at"]
    }

@api_router.post("/access/resend")
async def resend_access_code(data: ResendCodeRequest):
    query = {"email": data.email, "payment_status": "paid", "is_service": False}
    if data.product_id:
        query["product_id"] = data.product_id
    
    transaction = await db.payment_transactions.find_one(query, {"_id": 0}, sort=[("created_at", -1)])
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Aucun achat trouvé pour cet email")
    
    product = await db.products.find_one({"id": transaction["product_id"]}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    
    code = generate_access_code()
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=ACCESS_CODE_VALIDITY_HOURS)).isoformat()
    
    access_code = AccessCode(
        code=code,
        product_id=transaction["product_id"],
        email=data.email,
        order_id=transaction["id"],
        expires_at=expires_at
    )
    await db.access_codes.insert_one(access_code.model_dump())
    
    email_sent = await send_access_code_email(data.email, code, product["name"], ACCESS_CODE_VALIDITY_HOURS)
    
    if not email_sent:
        raise HTTPException(status_code=500, detail="Erreur lors de l'envoi de l'email")
    
    return {"success": True, "message": f"Nouveau code envoyé à {data.email}", "product_name": product["name"]}

# ==================== PORTFOLIO ROUTES ====================

@api_router.post("/portfolio/submit")
async def submit_portfolio(data: PortfolioSubmissionCreate):
    """Submit portfolio information (before payment)"""
    # Check if product exists and is a service
    product = await db.products.find_one({"id": data.product_id, "is_service": True}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Service non trouvé")
    
    # Create submission with pending payment
    submission = PortfolioSubmission(**data.model_dump())
    await db.portfolio_submissions.insert_one(submission.model_dump())
    
    return {
        "success": True, 
        "submission_id": submission.id,
        "message": "Informations enregistrées. Procédez au paiement."
    }

@api_router.post("/portfolio/pay/{submission_id}")
async def pay_for_portfolio(submission_id: str, request: Request):
    """Create payment session for a portfolio submission"""
    submission = await db.portfolio_submissions.find_one({"id": submission_id}, {"_id": 0})
    if not submission:
        raise HTTPException(status_code=404, detail="Soumission non trouvée")
    
    if submission.get("payment_status") == "paid":
        raise HTTPException(status_code=400, detail="Déjà payé")
    
    product = await db.products.find_one({"id": submission["product_id"]}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Service non trouvé")
    
    api_key = os.environ.get('STRIPE_API_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="Stripe non configuré")
    
    host_url = str(request.base_url).rstrip('/')
    webhook_url = f"{host_url}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=api_key, webhook_url=webhook_url)
    
    # Convert XOF to USD for Stripe
    amount_usd = product["price"] / 600 if product.get("currency") == "XOF" else product["price"]
    
    # Get origin from referer or default
    origin_url = request.headers.get("origin", "https://numstore.preview.emergentagent.com")
    
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
    
    # Update submission with session_id
    await db.portfolio_submissions.update_one(
        {"id": submission_id},
        {"$set": {"session_id": session.session_id}}
    )
    
    return {
        "checkout_url": session.url,
        "session_id": session.session_id
    }

@api_router.get("/portfolio/payment-status/{submission_id}")
async def check_portfolio_payment(submission_id: str, request: Request):
    """Check payment status for a portfolio submission"""
    submission = await db.portfolio_submissions.find_one({"id": submission_id}, {"_id": 0})
    if not submission:
        raise HTTPException(status_code=404, detail="Soumission non trouvée")
    
    if submission.get("payment_status") == "paid":
        return {"status": "paid", "message": "Paiement confirmé"}
    
    if not submission.get("session_id"):
        return {"status": "pending", "message": "En attente de paiement"}
    
    # Check with Stripe
    api_key = os.environ.get('STRIPE_API_KEY')
    if not api_key:
        return {"status": "pending"}
    
    host_url = str(request.base_url).rstrip('/')
    webhook_url = f"{host_url}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=api_key, webhook_url=webhook_url)
    
    try:
        status = await stripe_checkout.get_checkout_status(submission["session_id"])
        
        if status.payment_status == "paid":
            await db.portfolio_submissions.update_one(
                {"id": submission_id},
                {"$set": {"payment_status": "paid"}}
            )
            return {"status": "paid", "message": "Paiement confirmé"}
    except:
        pass
    
    return {"status": "pending", "message": "En attente de confirmation"}

@api_router.get("/portfolio/submission/{submission_id}")
async def get_portfolio_submission(submission_id: str):
    """Get portfolio submission by ID"""
    submission = await db.portfolio_submissions.find_one({"id": submission_id}, {"_id": 0})
    return submission

@api_router.get("/admin/portfolio-submissions")
async def get_all_portfolio_submissions(paid_only: bool = True):
    """Get all portfolio submissions for admin"""
    query = {"payment_status": "paid"} if paid_only else {}
    submissions = await db.portfolio_submissions.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return submissions

@api_router.put("/admin/portfolio-submissions/{submission_id}")
async def update_portfolio_submission(submission_id: str, status: str, portfolio_url: Optional[str] = None):
    """Update portfolio submission status"""
    update_data = {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}
    if portfolio_url:
        update_data["portfolio_url"] = portfolio_url
    
    result = await db.portfolio_submissions.update_one(
        {"id": submission_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Soumission non trouvée")
    
    # If completed with URL, send email to client
    if status == "completed" and portfolio_url:
        submission = await db.portfolio_submissions.find_one({"id": submission_id}, {"_id": 0})
        if submission and RESEND_API_KEY:
            try:
                params = {
                    "from": SENDER_EMAIL,
                    "to": [submission["email"]],
                    "subject": "🎉 Votre portfolio est prêt !",
                    "html": f"""
                    <div style="font-family: Arial; max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h1 style="color: #0055FF;">Votre portfolio est prêt !</h1>
                        <p>Bonjour {submission['full_name']},</p>
                        <p>Votre portfolio professionnel est maintenant disponible :</p>
                        <p><a href="{portfolio_url}" style="display: inline-block; background: #0055FF; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px;">Voir mon portfolio</a></p>
                        <p>Merci de votre confiance !</p>
                    </div>
                    """
                }
                await asyncio.to_thread(resend.Emails.send, params)
            except Exception as e:
                logger.error(f"Failed to send completion email: {e}")
    
    return {"success": True}

# ==================== ADMIN ROUTES ====================

ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

class AdminLogin(BaseModel):
    password: str

@api_router.post("/admin/login")
async def admin_login(data: AdminLogin):
    if data.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Mot de passe incorrect")
    return {"success": True, "token": "admin-authenticated"}

@api_router.get("/admin/stats")
async def get_admin_stats():
    paid_transactions = await db.payment_transactions.find({"payment_status": "paid"}, {"_id": 0}).to_list(10000)
    
    total_revenue_xof = sum(t["amount"] for t in paid_transactions if t.get("currency") == "XOF")
    total_revenue_usd = sum(t["amount"] for t in paid_transactions if t.get("currency") != "XOF")
    total_sales = len(paid_transactions)
    products_count = await db.products.count_documents({"is_active": True})
    portfolio_pending = await db.portfolio_submissions.count_documents({"status": "pending", "payment_status": "paid"})
    
    recent = await db.payment_transactions.find({"payment_status": "paid"}, {"_id": 0}).sort("created_at", -1).to_list(10)
    
    return {
        "total_revenue_xof": total_revenue_xof,
        "total_revenue_usd": total_revenue_usd,
        "total_sales": total_sales,
        "products_count": products_count,
        "portfolio_pending": portfolio_pending,
        "recent_transactions": recent
    }

@api_router.get("/admin/products")
async def admin_get_products():
    products = await db.products.find({}, {"_id": 0}).to_list(1000)
    return products

@api_router.post("/admin/products")
async def admin_create_product(data: ProductCreate):
    product = Product(**data.model_dump())
    await db.products.insert_one(product.model_dump())
    return product

@api_router.put("/admin/products/{product_id}")
async def admin_update_product(product_id: str, data: ProductCreate):
    update_data = data.model_dump()
    result = await db.products.update_one({"id": product_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    product = await db.products.find_one({"id": product_id}, {"_id": 0})
    return product

@api_router.delete("/admin/products/{product_id}")
async def admin_delete_product(product_id: str):
    result = await db.products.delete_one({"id": product_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    return {"success": True}

# ==================== SEED DATA ====================

@api_router.post("/seed")
async def seed_data():
    existing = await db.products.find_one({}, {"_id": 0})
    if existing:
        return {"message": "Données déjà initialisées"}
    
    products = [
        # === PORTFOLIO SERVICES ===
        Product(
            name="Portfolio Essentiel",
            description="Votre premier pas vers une presence digitale professionnelle. Site web one-page elegant avec presentation, parcours et competences.",
            price=25000,
            currency="XOF",
            category="portfolio",
            image_url="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400",
            is_service=True
        ),
        Product(
            name="Portfolio Premium",
            description="Portfolio web multi-pages avec design sur-mesure, animations fluides, integration reseaux sociaux, et support pendant 3 mois.",
            price=50000,
            currency="XOF",
            category="portfolio",
            image_url="https://images.unsplash.com/photo-1560250097-0b93528c311a?w=400",
            is_service=True
        ),
        Product(
            name="Pack VIP — Identite Digitale Complete",
            description="L'offre ultime. Portfolio web premium + CV digital interactif + carte de visite NFC digitale + optimisation LinkedIn + support 6 mois.",
            price=95000,
            currency="XOF",
            category="portfolio",
            image_url="https://static.prod-images.emergentagent.com/jobs/d92c6202-14d7-42b4-8759-6d0ad38d3b87/images/16027425fe7f4010eb33e27f710912ad6282ccd6141f0c28a8cc9161d05e3a70.png",
            is_service=True
        ),
        Product(
            name="Refonte CV Digital",
            description="Transformation de votre CV classique en un CV digital moderne et interactif. Format web responsive accessible via lien.",
            price=15000,
            currency="XOF",
            category="portfolio",
            image_url="https://images.unsplash.com/photo-1697292859784-c319e612ea15?w=400",
            is_service=True
        ),
        Product(
            name="Optimisation Profil LinkedIn",
            description="Audit complet et optimisation de votre profil LinkedIn: photo, banniere, resume, experiences, et mots-cles pour maximiser votre visibilite.",
            price=20000,
            currency="XOF",
            category="portfolio",
            image_url="https://images.unsplash.com/photo-1611944212129-29977ae1398c?w=400",
            is_service=True
        ),
        # === DIGITAL PRODUCTS ===
        Product(
            name="Guide Marketing Digital",
            description="E-book complet sur les strategies marketing digital modernes. 200 pages de conseils pratiques pour developper votre activite en ligne.",
            price=15000,
            currency="XOF",
            category="ebook",
            image_url="https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=400",
            file_size="15 MB"
        ),
        Product(
            name="Pack Templates CV Pro",
            description="10 templates de CV professionnels au format Word et PDF. Designs modernes et elegants, facilement personnalisables.",
            price=10000,
            currency="XOF",
            category="template",
            image_url="https://images.unsplash.com/photo-1586281380349-632531db7ed4?w=400",
            file_size="25 MB"
        ),
        Product(
            name="Guide Personal Branding",
            description="Comment construire et monetiser votre marque personnelle en Afrique francophone. Strategies, outils et etudes de cas.",
            price=12000,
            currency="XOF",
            category="ebook",
            image_url="https://images.unsplash.com/photo-1553484771-047a44eee27a?w=400",
            file_size="18 MB"
        ),
    ]
    
    for product in products:
        await db.products.insert_one(product.model_dump())
    
    return {"message": "Données initialisées", "products_count": len(products)}

@api_router.get("/")
async def root():
    return {"message": "NumStore API v2.1", "status": "running"}

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
