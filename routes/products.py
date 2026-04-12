"""
Routes API pour les produits.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
import asyncpg
import uuid
from datetime import datetime, timezone

from database import get_db
from models import Product, ProductCreate

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("", response_model=List[dict])
async def get_products(
    category: Optional[str] = None,
    db: asyncpg.Connection = Depends(get_db)
):
    """Liste tous les produits actifs."""
    if category:
        products = await db.fetch(
            "SELECT * FROM products WHERE is_active = true AND category = $1 ORDER BY created_at DESC",
            category
        )
    else:
        products = await db.fetch(
            "SELECT * FROM products WHERE is_active = true ORDER BY created_at DESC"
        )
    
    return [dict(p) for p in products]


@router.get("/{product_id}")
async def get_product(product_id: str, db: asyncpg.Connection = Depends(get_db)):
    """Récupère un produit par ID."""
    product = await db.fetchrow(
        "SELECT * FROM products WHERE id = $1",
        product_id
    )
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    
    return dict(product)


@router.post("/seed")
async def seed_products(db: asyncpg.Connection = Depends(get_db)):
    """Initialise les données de produits."""
    existing = await db.fetchval("SELECT COUNT(*) FROM products")
    if existing > 0:
        return {"message": "Données déjà initialisées"}
    
    products = [
        # === PORTFOLIO SERVICES ===
        {
            "id": str(uuid.uuid4()),
            "name": "Portfolio Essentiel",
            "description": "Votre premier pas vers une présence digitale professionnelle. Site web one-page élégant avec présentation, parcours et compétences.",
            "price": 25000,
            "currency": "XOF",
            "category": "portfolio",
            "image_url": "https://images.unsplash.com/photo-1642257834579-eee89ff3e9fd?w=400",
            "is_service": True,
            "is_active": True,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Portfolio Premium",
            "description": "Portfolio web multi-pages avec design sur-mesure, animations fluides, intégration réseaux sociaux, et support pendant 3 mois.",
            "price": 50000,
            "currency": "XOF",
            "category": "portfolio",
            "image_url": "https://images.unsplash.com/photo-1763739528307-ad10867048b3?w=400",
            "is_service": True,
            "is_active": True,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Pack VIP — Identité Digitale Complète",
            "description": "L'offre ultime. Portfolio web premium + CV digital interactif + carte de visite NFC digitale + optimisation LinkedIn + support 6 mois.",
            "price": 95000,
            "currency": "XOF",
            "category": "portfolio",
            "image_url": "https://images.unsplash.com/photo-1632255657991-ce622acebecd?w=400",
            "is_service": True,
            "is_active": True,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Refonte CV Digital",
            "description": "Transformation de votre CV classique en un CV digital moderne et interactif. Format web responsive accessible via lien.",
            "price": 15000,
            "currency": "XOF",
            "category": "portfolio",
            "image_url": "https://images.unsplash.com/photo-1678282342910-a135f7b900ae?w=400",
            "is_service": True,
            "is_active": True,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Optimisation Profil LinkedIn",
            "description": "Audit complet et optimisation de votre profil LinkedIn: photo, bannière, résumé, expériences, et mots-clés pour maximiser votre visibilité.",
            "price": 20000,
            "currency": "XOF",
            "category": "portfolio",
            "image_url": "https://images.unsplash.com/photo-1758519290311-7e6ddb194016?w=400",
            "is_service": True,
            "is_active": True,
            "created_at": datetime.now(timezone.utc)
        },
        # === DIGITAL PRODUCTS ===
        {
            "id": str(uuid.uuid4()),
            "name": "Guide Marketing Digital",
            "description": "E-book complet sur les stratégies marketing digital modernes. 200 pages de conseils pratiques pour développer votre activité en ligne.",
            "price": 15000,
            "currency": "XOF",
            "category": "ebook",
            "image_url": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=400",
            "file_size": "15 MB",
            "is_service": False,
            "is_active": True,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Pack Templates CV Pro",
            "description": "10 templates de CV professionnels au format Word et PDF. Designs modernes et élégants, facilement personnalisables.",
            "price": 10000,
            "currency": "XOF",
            "category": "template",
            "image_url": "https://images.unsplash.com/photo-1586281380349-632531db7ed4?w=400",
            "file_size": "25 MB",
            "is_service": False,
            "is_active": True,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Guide Personal Branding",
            "description": "Comment construire et monétiser votre marque personnelle en Afrique francophone. Stratégies, outils et études de cas.",
            "price": 12000,
            "currency": "XOF",
            "category": "ebook",
            "image_url": "https://images.unsplash.com/photo-1553484771-047a44eee27a?w=400",
            "file_size": "18 MB",
            "is_service": False,
            "is_active": True,
            "created_at": datetime.now(timezone.utc)
        },
    ]
    
    for p in products:
        await db.execute(
            """INSERT INTO products (id, name, description, price, currency, category, image_url, download_url, file_size, is_service, is_active, created_at)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)""",
            p["id"], p["name"], p["description"], p["price"], p["currency"], p["category"],
            p.get("image_url"), p.get("download_url"), p.get("file_size"),
            p.get("is_service", False), p.get("is_active", True), p["created_at"]
        )
    
    return {"message": "Données initialisées", "products_count": len(products)}
