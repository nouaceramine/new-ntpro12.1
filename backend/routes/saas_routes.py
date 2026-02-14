"""
SaaS Routes - Complete Multi-tenant Management
Extracted from server.py for better code organization
Contains: Plans, Tenants, Agents, Databases, Registration
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, Field, EmailStr
import uuid
import jwt
import bcrypt
import logging
import io
import json
import os

logger = logging.getLogger(__name__)

# Database imports
from config.database import db, main_db, client, get_tenant_db, init_tenant_database

# JWT Settings
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
ALGORITHM = "HS256"

security = HTTPBearer()

# Create router with prefix
router = APIRouter(tags=["SaaS Admin"])

# ============ PYDANTIC MODELS ============

class PlanFeatures(BaseModel):
    max_products: int = 100
    max_users: int = 3
    max_warehouses: int = 1
    has_pos: bool = True
    has_inventory: bool = True
    has_reports: bool = True
    has_multi_warehouse: bool = False
    has_api_access: bool = False
    has_ecommerce: bool = False
    has_woocommerce: bool = False
    has_advanced_reports: bool = False
    has_employee_management: bool = False
    has_debt_management: bool = True
    has_customer_loyalty: bool = False
    has_supplier_management: bool = True
    has_email_notifications: bool = False
    has_sms_notifications: bool = False

class PlanCreate(BaseModel):
    name: str
    name_ar: str = ""
    description: str = ""
    description_ar: str = ""
    monthly_price: float = 0
    yearly_price: float = 0
    six_month_price: float = 0
    features: PlanFeatures = Field(default_factory=PlanFeatures)
    is_active: bool = True
    sort_order: int = 0
    is_popular: bool = False
    badge: str = ""
    badge_ar: str = ""

class PlanUpdate(BaseModel):
    name: Optional[str] = None
    name_ar: Optional[str] = None
    description: Optional[str] = None
    description_ar: Optional[str] = None
    monthly_price: Optional[float] = None
    yearly_price: Optional[float] = None
    six_month_price: Optional[float] = None
    features: Optional[PlanFeatures] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None
    is_popular: Optional[bool] = None
    badge: Optional[str] = None
    badge_ar: Optional[str] = None

class PlanResponse(BaseModel):
    id: str
    name: str
    name_ar: str = ""
    description: str = ""
    description_ar: str = ""
    monthly_price: float = 0
    yearly_price: float = 0
    six_month_price: float = 0
    features: dict = {}
    is_active: bool = True
    sort_order: int = 0
    is_popular: bool = False
    badge: str = ""
    badge_ar: str = ""
    created_at: Optional[str] = None

class TenantStats(BaseModel):
    products: int = 0
    users: int = 0
    sales: int = 0

class TenantCreate(BaseModel):
    name: str
    email: str
    password: str
    phone: str = ""
    company_name: str = ""
    plan_id: str
    subscription_type: str = "monthly"
    agent_id: Optional[str] = None
    business_type: str = "retailer"
    role: str = "admin"

class TenantUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company_name: Optional[str] = None
    plan_id: Optional[str] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None
    features_override: Optional[dict] = None
    limits_override: Optional[dict] = None

class TenantResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: str = ""
    company_name: str = ""
    plan_id: Optional[str] = None
    plan_name: str = ""
    agent_id: Optional[str] = None
    agent_name: str = ""
    is_active: bool = True
    is_trial: bool = False
    trial_ends_at: Optional[str] = None
    subscription_type: str = "monthly"
    subscription_starts_at: Optional[str] = None
    subscription_ends_at: Optional[str] = None
    features_override: dict = {}
    limits_override: dict = {}
    notes: str = ""
    stats: TenantStats = Field(default_factory=TenantStats)
    business_type: str = "retailer"
    database_initialized: bool = False
    created_at: Optional[str] = None

    class Config:
        from_attributes = True

class SubscriptionPayment(BaseModel):
    amount: float
    payment_method: str = "cash"
    subscription_type: str = "monthly"
    notes: str = ""
    transaction_id: str = ""

class SubscriptionPaymentResponse(BaseModel):
    id: str
    tenant_id: str
    tenant_name: str = ""
    amount: float
    payment_method: str = "cash"
    subscription_type: str = "monthly"
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    notes: str = ""
    transaction_id: str = ""
    created_by: str = ""
    created_at: Optional[str] = None

class AgentCreate(BaseModel):
    name: str
    email: str
    password: str
    phone: str = ""
    commission_rate: float = 10.0
    notes: str = ""
    is_active: bool = True

class AgentUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    commission_rate: Optional[float] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None

class AgentResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: str = ""
    commission_rate: float = 10.0
    total_earnings: float = 0
    pending_earnings: float = 0
    paid_earnings: float = 0
    tenants_count: int = 0
    notes: str = ""
    is_active: bool = True
    created_at: Optional[str] = None

class AgentTransactionCreate(BaseModel):
    type: str  # "commission" or "payout"
    amount: float
    tenant_id: Optional[str] = None
    notes: str = ""

class AgentTransactionResponse(BaseModel):
    id: str
    agent_id: str
    type: str
    amount: float
    tenant_id: Optional[str] = None
    tenant_name: str = ""
    notes: str = ""
    created_at: Optional[str] = None

class AgentLoginRequest(BaseModel):
    email: str
    password: str

# ============ HELPER FUNCTIONS ============

def create_access_token(data: dict) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=30)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_super_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Check if user is super admin"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        user = await main_db.users.find_one({"id": user_id})
        if not user or user.get("role") not in ["super_admin", "saas_admin"]:
            raise HTTPException(status_code=403, detail="Super admin access required")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user_optional(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user (optional auth)"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except:
        return None


# ============ PLANS ROUTES ============

@router.get("/saas/plans", response_model=List[PlanResponse])
async def get_plans(include_inactive: bool = False):
    """Get all subscription plans (public)"""
    query = {} if include_inactive else {"is_active": True}
    plans = await db.saas_plans.find(query, {"_id": 0}).sort("sort_order", 1).to_list(100)
    return [PlanResponse(**p) for p in plans]

@router.get("/saas/plans/public")
async def get_public_plans():
    """Get active plans for public pricing page - no auth required"""
    plans = await db.saas_plans.find({"is_active": True}, {"_id": 0}).sort("sort_order", 1).to_list(100)
    return plans

@router.get("/saas/plans/{plan_id}", response_model=PlanResponse)
async def get_plan(plan_id: str):
    """Get a specific plan"""
    plan = await db.saas_plans.find_one({"id": plan_id}, {"_id": 0})
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return PlanResponse(**plan)

@router.post("/saas/plans", response_model=PlanResponse)
async def create_plan(plan: PlanCreate, admin: dict = Depends(get_super_admin)):
    """Create a new subscription plan"""
    plan_doc = {
        "id": str(uuid.uuid4()),
        **plan.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.saas_plans.insert_one(plan_doc)
    return PlanResponse(**{k: v for k, v in plan_doc.items() if k != "_id"})

@router.put("/saas/plans/{plan_id}", response_model=PlanResponse)
async def update_plan(plan_id: str, updates: PlanUpdate, admin: dict = Depends(get_super_admin)):
    """Update a subscription plan"""
    plan = await db.saas_plans.find_one({"id": plan_id})
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.saas_plans.update_one({"id": plan_id}, {"$set": update_data})
    updated = await db.saas_plans.find_one({"id": plan_id}, {"_id": 0})
    return PlanResponse(**updated)

@router.delete("/saas/plans/{plan_id}")
async def delete_plan(plan_id: str, admin: dict = Depends(get_super_admin)):
    """Delete a subscription plan"""
    result = await db.saas_plans.delete_one({"id": plan_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Plan not found")
    return {"message": "Plan deleted successfully"}

