"""
Routes des pages (templates Jinja2).
"""

import os
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
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


def record_to_dict(row) -> dict:
    """Convertit un asyncpg.Record en dictionnaire propre."""
    if row is None:
        return None
    result = {}
    for key in row.keys():
        value = row[key]
        # Convertir Decimal en float pour éviter les problèmes de sérialisation
        if hasattr(value, '__float__'):
            try:
                result[key] = float(value)
            except:
                result[key] = value
        else:
            result[key] = value
    return result


def records_to_list(rows) -> list:
    """Convertit une liste de asyncpg.Record en liste de dictionnaires."""
    return [record_to_dict(row) for row in rows]


# Ajoute le helper aux templates
templates.env.globals["format_price"] = format_price


@router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: asyncpg.Connection = Depends(get_db)):
    """Page d'accueil avec produits."""
    rows = await db.fetch("SELECT * FROM products WHERE is_active = true ORDER BY created_at DESC")
    products = records_to_list(rows)

    portfolio_products = [p for p in products if p.get("is_service") is True]
    digital_products = [p for p in products if p.get("is_service") is not True]

    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={
            "portfolio_products": portfolio_products,
            "digital_products": digital_products
        }
    )


@router.get("/product/{product_id}", response_class=HTMLResponse)
async def product_page(request: Request, product_id: str, db: asyncpg.Connection = Depends(get_db)):
    """Page détail produit."""
    row = await db.fetchrow("SELECT * FROM products WHERE id = $1 AND is_active = true", product_id)
    if not row:
        return templates.TemplateResponse(
            request=request,
            name="404.html",
            context={},
            status_code=404
        )

    return templates.TemplateResponse(
        request=request,
        name="product.html",
        context={"product": record_to_dict(row)}
    )


@router.get("/access", response_class=HTMLResponse)
async def access_page(request: Request):
    """Page d'accès avec code."""
    # Paystack renvoie 'reference', on accepte aussi 'session_id' pour compatibilité
    reference = request.query_params.get("reference") or request.query_params.get("session_id")
    product_id = request.query_params.get("product_id")

    return templates.TemplateResponse(
        request=request,
        name="access.html",
        context={
            "reference": reference,
            "product_id": product_id
        }
    )
            "product_id": product_id
        }
    )


@router.get("/portfolio/form", response_class=HTMLResponse)
async def portfolio_form_page(request: Request, db: asyncpg.Connection = Depends(get_db)):
    """Formulaire portfolio."""
    product_id = request.query_params.get("product_id")
    email = request.query_params.get("email", "")

    product = None
    if product_id:
        row = await db.fetchrow("SELECT * FROM products WHERE id = $1 AND is_service = true", product_id)
        product = record_to_dict(row)

    return templates.TemplateResponse(
        request=request,
        name="portfolio_form.html",
        context={
            "product": product,
            "email": email
        }
    )


@router.get("/portfolio/success", response_class=HTMLResponse)
async def portfolio_success_page(request: Request, db: asyncpg.Connection = Depends(get_db)):
    """Page succès portfolio."""
    submission_id = request.query_params.get("submission_id")

    submission = None
    if submission_id:
        row = await db.fetchrow("SELECT * FROM portfolio_submissions WHERE id = $1", submission_id)
        submission = record_to_dict(row)

    return templates.TemplateResponse(
        request=request,
        name="portfolio_success.html",
        context={"submission": submission}
    )


@router.get("/admin", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    """Page login admin."""
    admin = get_admin_user(request)
    if admin:
        return RedirectResponse("/admin/dashboard", status_code=302)

    return templates.TemplateResponse(
        request=request,
        name="admin_login.html",
        context={}
    )


@router.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard_page(request: Request, db: asyncpg.Connection = Depends(get_db)):
    """Dashboard admin."""
    admin = get_admin_user(request)
    if not admin:
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

    rows = await db.fetch(
        """SELECT * FROM payment_transactions 
           WHERE payment_status = 'paid' 
           ORDER BY created_at DESC LIMIT 10"""
    )

    return templates.TemplateResponse(
        request=request,
        name="admin_dashboard.html",
        context={
            "total_revenue": float(total_revenue) if total_revenue else 0,
            "total_sales": total_sales or 0,
            "products_count": products_count or 0,
            "portfolio_pending": portfolio_pending or 0,
            "recent_transactions": records_to_list(rows)
        }
    )


@router.get("/admin/products", response_class=HTMLResponse)
async def admin_products_page(request: Request, db: asyncpg.Connection = Depends(get_db)):
    """Gestion produits admin."""
    admin = get_admin_user(request)
    if not admin:
        return RedirectResponse("/admin", status_code=302)

    rows = await db.fetch("SELECT * FROM products ORDER BY created_at DESC")

    return templates.TemplateResponse(
        request=request,
        name="admin_products.html",
        context={"products": records_to_list(rows)}
    )


@router.get("/admin/portfolios", response_class=HTMLResponse)
async def admin_portfolios_page(request: Request, db: asyncpg.Connection = Depends(get_db)):
    """Gestion portfolios admin."""
    admin = get_admin_user(request)
    if not admin:
        return RedirectResponse("/admin", status_code=302)

    rows = await db.fetch(
        """SELECT * FROM portfolio_submissions 
           WHERE payment_status = 'paid' 
           ORDER BY created_at DESC"""
    )

    return templates.TemplateResponse(
        request=request,
        name="admin_portfolios.html",
        context={"submissions": records_to_list(rows)}
    )