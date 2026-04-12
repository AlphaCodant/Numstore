"""
Routes API admin.
"""

import os
import uuid
import json
import shutil
import logging
from pathlib import Path
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, Response, UploadFile, File
from fastapi.responses import RedirectResponse, FileResponse
import asyncpg

from database import get_db
from models import AdminLogin, ProductCreate
from auth import create_access_token, get_admin_user
from email_utils import send_portfolio_completion_email

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["admin"])

ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')
UPLOADS_DIR = Path(__file__).parent.parent / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_EXTENSIONS = {'.pdf', '.ppt', '.pptx', '.doc', '.docx', '.xls', '.xlsx', '.zip', '.rar', '.epub', '.txt', '.csv'}


@router.post("/login")
async def admin_login(data: AdminLogin, response: Response):
    """Connexion admin."""
    if data.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Mot de passe incorrect")
    
    token = create_access_token({"role": "admin"})
    response.set_cookie(
        key="admin_token",
        value=token,
        httponly=True,
        max_age=7200,  # 2 heures
        samesite="lax"
    )
    
    return {"success": True, "token": token}


@router.post("/logout")
async def admin_logout(response: Response):
    """Déconnexion admin."""
    response.delete_cookie("admin_token")
    return {"success": True}


@router.get("/stats")
async def get_admin_stats(request: Request, db: asyncpg.Connection = Depends(get_db)):
    """Statistiques admin."""
    admin = get_admin_user(request)
    if not admin:
        raise HTTPException(status_code=401, detail="Non autorisé")
    
    total_revenue_xof = await db.fetchval(
        "SELECT COALESCE(SUM(amount), 0) FROM payment_transactions WHERE payment_status = 'paid' AND currency = 'XOF'"
    )
    total_revenue_usd = await db.fetchval(
        "SELECT COALESCE(SUM(amount), 0) FROM payment_transactions WHERE payment_status = 'paid' AND currency != 'XOF'"
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
    
    return {
        "total_revenue_xof": total_revenue_xof or 0,
        "total_revenue_usd": total_revenue_usd or 0,
        "total_sales": total_sales or 0,
        "products_count": products_count or 0,
        "portfolio_pending": portfolio_pending or 0,
        "recent_transactions": [dict(t) for t in recent_transactions]
    }


@router.get("/products")
async def admin_get_products(request: Request, db: asyncpg.Connection = Depends(get_db)):
    """Liste tous les produits (admin)."""
    admin = get_admin_user(request)
    if not admin:
        raise HTTPException(status_code=401, detail="Non autorisé")
    
    products = await db.fetch("SELECT * FROM products ORDER BY created_at DESC")
    return [dict(p) for p in products]


@router.post("/products")
async def admin_create_product(data: ProductCreate, request: Request, db: asyncpg.Connection = Depends(get_db)):
    """Crée un nouveau produit."""
    admin = get_admin_user(request)
    if not admin:
        raise HTTPException(status_code=401, detail="Non autorisé")
    
    product_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    
    await db.execute(
        """INSERT INTO products (id, name, description, price, currency, category, image_url, download_url, file_size, is_service, is_active, created_at)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)""",
        product_id, data.name, data.description, data.price, data.currency, data.category,
        data.image_url, data.download_url, data.file_size, data.is_service, True, now
    )
    
    product = await db.fetchrow("SELECT * FROM products WHERE id = $1", product_id)
    return dict(product)


@router.put("/products/{product_id}")
async def admin_update_product(product_id: str, data: ProductCreate, request: Request, db: asyncpg.Connection = Depends(get_db)):
    """Met à jour un produit."""
    admin = get_admin_user(request)
    if not admin:
        raise HTTPException(status_code=401, detail="Non autorisé")
    
    result = await db.execute(
        """UPDATE products SET name = $2, description = $3, price = $4, currency = $5, category = $6,
           image_url = $7, download_url = $8, file_size = $9, is_service = $10
           WHERE id = $1""",
        product_id, data.name, data.description, data.price, data.currency, data.category,
        data.image_url, data.download_url, data.file_size, data.is_service
    )
    
    product = await db.fetchrow("SELECT * FROM products WHERE id = $1", product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    
    return dict(product)


@router.delete("/products/{product_id}")
async def admin_delete_product(product_id: str, request: Request, db: asyncpg.Connection = Depends(get_db)):
    """Supprime un produit."""
    admin = get_admin_user(request)
    if not admin:
        raise HTTPException(status_code=401, detail="Non autorisé")
    
    # Delete associated file if exists
    product = await db.fetchrow("SELECT download_url FROM products WHERE id = $1", product_id)
    if product and product["download_url"] and product["download_url"].startswith("/api/admin/files/"):
        filename = product["download_url"].split("/")[-1]
        filepath = UPLOADS_DIR / filename
        if filepath.exists():
            filepath.unlink()
    
    await db.execute("DELETE FROM products WHERE id = $1", product_id)
    return {"success": True}


@router.post("/upload")
async def admin_upload_file(request: Request, file: UploadFile = File(...), db: asyncpg.Connection = Depends(get_db)):
    """Upload un fichier pour un produit numerique."""
    admin = get_admin_user(request)
    if not admin:
        raise HTTPException(status_code=401, detail="Non autorise")
    
    # Validate extension
    original_name = file.filename or "fichier"
    ext = Path(original_name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Type de fichier non autorise. Extensions acceptees: {', '.join(ALLOWED_EXTENSIONS)}")
    
    # Read file content
    content = await file.read()
    
    # Validate size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Fichier trop volumineux (max 50 MB)")
    
    # Generate unique filename
    unique_name = f"{uuid.uuid4().hex}{ext}"
    filepath = UPLOADS_DIR / unique_name
    
    # Save file
    with open(filepath, "wb") as f:
        f.write(content)
    
    # Calculate human-readable size
    size_bytes = len(content)
    if size_bytes < 1024:
        file_size = f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        file_size = f"{size_bytes / 1024:.0f} KB"
    else:
        file_size = f"{size_bytes / (1024 * 1024):.1f} MB"
    
    download_url = f"/api/admin/files/{unique_name}"
    
    logger.info(f"File uploaded: {original_name} -> {unique_name} ({file_size})")
    
    return {
        "success": True,
        "filename": unique_name,
        "original_name": original_name,
        "download_url": download_url,
        "file_size": file_size
    }


@router.get("/files/{filename}")
async def admin_serve_file(filename: str, request: Request):
    """Sert un fichier uploade (acces admin uniquement pour preview)."""
    admin = get_admin_user(request)
    if not admin:
        raise HTTPException(status_code=401, detail="Non autorise")
    
    filepath = UPLOADS_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Fichier non trouve")
    
    return FileResponse(filepath, filename=filename)


@router.get("/portfolio-submissions")
async def get_all_portfolio_submissions(
    request: Request,
    paid_only: bool = True,
    db: asyncpg.Connection = Depends(get_db)
):
    """Liste les soumissions de portfolio."""
    admin = get_admin_user(request)
    if not admin:
        raise HTTPException(status_code=401, detail="Non autorisé")
    
    if paid_only:
        submissions = await db.fetch(
            """SELECT * FROM portfolio_submissions 
               WHERE payment_status = 'paid' 
               ORDER BY created_at DESC"""
        )
    else:
        submissions = await db.fetch("SELECT * FROM portfolio_submissions ORDER BY created_at DESC")
    
    results = []
    for s in submissions:
        result = dict(s)
        for field in ['skills', 'experiences', 'education', 'projects']:
            if result.get(field) and isinstance(result[field], str):
                result[field] = json.loads(result[field])
        results.append(result)
    
    return results


@router.put("/portfolio-submissions/{submission_id}")
async def update_portfolio_submission(
    submission_id: str,
    status: str,
    portfolio_url: str = None,
    request: Request = None,
    db: asyncpg.Connection = Depends(get_db)
):
    """Met à jour le statut d'une soumission."""
    admin = get_admin_user(request)
    if not admin:
        raise HTTPException(status_code=401, detail="Non autorisé")
    
    now = datetime.now(timezone.utc)
    
    if portfolio_url:
        await db.execute(
            "UPDATE portfolio_submissions SET status = $2, portfolio_url = $3, updated_at = $4 WHERE id = $1",
            submission_id, status, portfolio_url, now
        )
    else:
        await db.execute(
            "UPDATE portfolio_submissions SET status = $2, updated_at = $3 WHERE id = $1",
            submission_id, status, now
        )
    
    submission = await db.fetchrow("SELECT * FROM portfolio_submissions WHERE id = $1", submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Soumission non trouvée")
    
    # Envoie l'email si terminé avec URL
    if status == "completed" and portfolio_url:
        await send_portfolio_completion_email(
            submission["email"],
            submission["full_name"],
            portfolio_url
        )
    
    return {"success": True}
