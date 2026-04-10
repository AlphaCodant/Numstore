"""
Routes des pages (templates Jinja2).
"""

import os
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import asyncpg

from database import get_db
from auth import get_admin_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def format_price(price: float, currency: str = "XOF") -> str:
    """Formate le prix avec devise."""
    if currency == "XOF":
        return f"{int(price):,} FCFA".replace(",", " ")
    return f"${price:.2f}"


# Ajoute le helper aux templates
templates.env.globals["format_price"] = format_price


@router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: asyncpg.Connection = Depends(get_db)):
    """Page d'accueil avec produits."""
    products = await db.fetch("SELECT * FROM products WHERE is_active = true ORDER BY created_at DESC")
    portfolio_products = [dict(p) for p in products if p["is_service"]]
    digital_products = [dict(p) for p in products if not p["is_service"]]
    
    return templates.TemplateResponse("home.html", {
        "request": request,
        "portfolio_products": portfolio_products,
        "digital_products": digital_products
    })


@router.get("/product/{product_id}", response_class=HTMLResponse)
async def product_page(request: Request, product_id: str, db: asyncpg.Connection = Depends(get_db)):
    """Page détail produit."""
    product = await db.fetchrow("SELECT * FROM products WHERE id = $1 AND is_active = true", product_id)
    if not product:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)
    
    return templates.TemplateResponse("product.html", {
        "request": request,
        "product": dict(product)
    })


@router.get("/access", response_class=HTMLResponse)
async def access_page(request: Request):
    """Page d'accès avec code."""
    session_id = request.query_params.get("session_id")
    product_id = request.query_params.get("product_id")
    
    return templates.TemplateResponse("access.html", {
        "request": request,
        "session_id": session_id,
        "product_id": product_id
    })


@router.get("/portfolio/form", response_class=HTMLResponse)
async def portfolio_form_page(request: Request, db: asyncpg.Connection = Depends(get_db)):
    """Formulaire portfolio."""
    product_id = request.query_params.get("product_id")
    email = request.query_params.get("email", "")
    
    product = None
    if product_id:
        product = await db.fetchrow("SELECT * FROM products WHERE id = $1 AND is_service = true", product_id)
        if product:
            product = dict(product)
    
    return templates.TemplateResponse("portfolio_form.html", {
        "request": request,
        "product": product,
        "email": email
    })


@router.get("/portfolio/success", response_class=HTMLResponse)
async def portfolio_success_page(request: Request, db: asyncpg.Connection = Depends(get_db)):
    """Page succès portfolio."""
    submission_id = request.query_params.get("submission_id")
    
    submission = None
    if submission_id:
        submission = await db.fetchrow("SELECT * FROM portfolio_submissions WHERE id = $1", submission_id)
        if submission:
            submission = dict(submission)
    
    return templates.TemplateResponse("portfolio_success.html", {
        "request": request,
        "submission": submission
    })


@router.get("/admin", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    """Page login admin."""
    admin = get_admin_user(request)
    if admin:
        from fastapi.responses import RedirectResponse
        return RedirectResponse("/admin/dashboard", status_code=302)
    
    return templates.TemplateResponse("admin_login.html", {"request": request})


@router.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard_page(request: Request, db: asyncpg.Connection = Depends(get_db)):
    """Dashboard admin."""
    admin = get_admin_user(request)
    if not admin:
        from fastapi.responses import RedirectResponse
        return RedirectResponse("/admin", status_code=302)
    
    # Stats
    total_revenue = await db.fetchval(
        "SELECT COALESCE(SUM(amount), 0) FROM payment_transactions WHERE payment_status = 'paid' AND currency = 'XOF'"
    )
    total_sales = await db.fetchval(
        "SELECT COUNT(*) FROM payment_transactions WHERE payment_status = 'paid'"
    )
    products_count = await db.fetchval("SELECT COUNT(*) FROM products WHERE is_active = true")
    portfolio_pending = await db.fetchval(
        "SELECT COUNT(*) FROM portfolio_submissions WHERE status = 'pending' AND payment_status = 'paid'"
    )
    
    recent_transactions = await db.fetch(
        """SELECT * FROM payment_transactions 
           WHERE payment_status = 'paid' 
           ORDER BY created_at DESC LIMIT 10"""
    )
    
    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request,
        "total_revenue": total_revenue or 0,
        "total_sales": total_sales or 0,
        "products_count": products_count or 0,
        "portfolio_pending": portfolio_pending or 0,
        "recent_transactions": [dict(t) for t in recent_transactions]
    })


@router.get("/admin/products", response_class=HTMLResponse)
async def admin_products_page(request: Request, db: asyncpg.Connection = Depends(get_db)):
    """Gestion produits admin."""
    admin = get_admin_user(request)
    if not admin:
        from fastapi.responses import RedirectResponse
        return RedirectResponse("/admin", status_code=302)
    
    products = await db.fetch("SELECT * FROM products ORDER BY created_at DESC")
    
    return templates.TemplateResponse("admin_products.html", {
        "request": request,
        "products": [dict(p) for p in products]
    })


@router.get("/admin/portfolios", response_class=HTMLResponse)
async def admin_portfolios_page(request: Request, db: asyncpg.Connection = Depends(get_db)):
    """Gestion portfolios admin."""
    admin = get_admin_user(request)
    if not admin:
        from fastapi.responses import RedirectResponse
        return RedirectResponse("/admin", status_code=302)
    
    submissions = await db.fetch(
        """SELECT * FROM portfolio_submissions 
           WHERE payment_status = 'paid' 
           ORDER BY created_at DESC"""
    )
    
    return templates.TemplateResponse("admin_portfolios.html", {
        "request": request,
        "submissions": [dict(s) for s in submissions]
    })
