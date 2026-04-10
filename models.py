"""
Modèles Pydantic pour NumStore.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict
from datetime import datetime
import uuid


# ==================== PRODUCTS ====================

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


class Product(BaseModel):
    id: str
    name: str
    description: str
    price: float
    currency: str = "XOF"
    category: str
    image_url: Optional[str] = None
    download_url: Optional[str] = None
    file_size: Optional[str] = None
    is_service: bool = False
    is_active: bool = True
    created_at: datetime


# ==================== PAYMENTS ====================

class PaymentRequest(BaseModel):
    product_id: str
    email: EmailStr
    origin_url: str


class PaymentTransaction(BaseModel):
    id: str
    session_id: str
    product_id: str
    amount: float
    currency: str = "XOF"
    email: str
    payment_status: str = "pending"
    access_code_sent: bool = False
    is_service: bool = False
    created_at: datetime


# ==================== ACCESS CODES ====================

class AccessCode(BaseModel):
    id: str
    code: str
    product_id: str
    email: str
    order_id: str
    created_at: datetime
    expires_at: datetime
    is_used: bool = False


class AccessRequest(BaseModel):
    code: str


class ResendCodeRequest(BaseModel):
    email: EmailStr
    product_id: Optional[str] = None


# ==================== PORTFOLIO ====================

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


class PortfolioSubmission(BaseModel):
    id: str
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
    payment_status: str = "pending"
    session_id: Optional[str] = None
    status: str = "pending"
    portfolio_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# ==================== ADMIN ====================

class AdminLogin(BaseModel):
    password: str
