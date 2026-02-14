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


# ============ TENANTS ROUTES ============

@router.get("/saas/tenants", response_model=List[TenantResponse])
async def get_tenants(admin: dict = Depends(get_super_admin)):
    """Get all tenants"""
    tenants = await db.saas_tenants.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    agents_list = await db.saas_agents.find({}, {"_id": 0, "id": 1, "name": 1}).to_list(1000)
    agents_map = {a["id"]: a["name"] for a in agents_list}
    
    for tenant in tenants:
        plan = await db.saas_plans.find_one({"id": tenant.get("plan_id")}, {"_id": 0, "name": 1, "name_ar": 1})
        tenant["plan_name"] = plan.get("name_ar", "") if plan else ""
        agent_id = tenant.get("agent_id")
        tenant["agent_name"] = agents_map.get(agent_id, "") if agent_id else ""
        
        tenant_db = client[f"tenant_{tenant['id'].replace('-', '_')}"]
        products_count = await tenant_db.products.count_documents({})
        users_count = await tenant_db.users.count_documents({})
        sales_count = await tenant_db.sales.count_documents({})
        tenant["stats"] = {"products": products_count, "users": users_count, "sales": sales_count}
    
    return [TenantResponse(**t) for t in tenants]

@router.get("/saas/tenants/{tenant_id}", response_model=TenantResponse)
async def get_tenant(tenant_id: str, admin: dict = Depends(get_super_admin)):
    """Get a specific tenant"""
    tenant = await db.saas_tenants.find_one({"id": tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    plan = await db.saas_plans.find_one({"id": tenant.get("plan_id")}, {"_id": 0, "name_ar": 1})
    tenant["plan_name"] = plan.get("name_ar", "") if plan else ""
    
    tenant_db = client[f"tenant_{tenant['id'].replace('-', '_')}"]
    products_count = await tenant_db.products.count_documents({})
    users_count = await tenant_db.users.count_documents({})
    sales_count = await tenant_db.sales.count_documents({})
    tenant["stats"] = {"products": products_count, "users": users_count, "sales": sales_count}
    
    return TenantResponse(**tenant)

@router.post("/saas/impersonate/{tenant_id}")
async def impersonate_tenant(tenant_id: str, admin: dict = Depends(get_super_admin)):
    """Generate a login token to impersonate a tenant"""
    tenant = await main_db.saas_tenants.find_one({"id": tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="المشترك غير موجود")
    
    if not tenant.get("is_active"):
        raise HTTPException(status_code=400, detail="حساب المشترك معطل")
    
    access_token = create_access_token({
        "sub": tenant_id,
        "email": tenant["email"],
        "role": "admin",
        "type": "tenant",
        "tenant_id": tenant_id
    })
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "email": tenant["email"],
        "name": tenant.get("name", ""),
        "company_name": tenant.get("company_name", ""),
        "tenant_id": tenant_id,
        "user_type": "tenant",
        "user": {
            "id": tenant_id,
            "email": tenant["email"],
            "name": tenant.get("name", ""),
            "role": "admin",
            "tenant_id": tenant_id,
            "company_name": tenant.get("company_name", ""),
            "database_name": tenant.get("database_name", "")
        }
    }

@router.post("/saas/tenants", response_model=TenantResponse)
async def create_tenant(tenant: TenantCreate, admin: dict = Depends(get_super_admin)):
    """Create a new tenant"""
    existing = await db.saas_tenants.find_one({"email": tenant.email})
    if existing:
        raise HTTPException(status_code=400, detail="البريد الإلكتروني مستخدم بالفعل")
    
    plan = await db.saas_plans.find_one({"id": tenant.plan_id}, {"_id": 0})
    if not plan:
        raise HTTPException(status_code=404, detail="الخطة غير موجودة")
    
    now = datetime.now(timezone.utc)
    if tenant.subscription_type == "monthly":
        ends_at = now + timedelta(days=30)
    elif tenant.subscription_type == "6months":
        ends_at = now + timedelta(days=180)
    else:
        ends_at = now + timedelta(days=365)
    
    tenant_id = str(uuid.uuid4())
    hashed_password = bcrypt.hashpw(tenant.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    tenant_doc = {
        "id": tenant_id,
        "name": tenant.name,
        "email": tenant.email,
        "phone": tenant.phone or "",
        "company_name": tenant.company_name or "",
        "password": hashed_password,
        "plan_id": tenant.plan_id,
        "agent_id": tenant.agent_id if hasattr(tenant, 'agent_id') else None,
        "is_active": True,
        "is_trial": False,
        "trial_ends_at": None,
        "subscription_type": tenant.subscription_type,
        "subscription_starts_at": now.isoformat(),
        "subscription_ends_at": ends_at.isoformat(),
        "features_override": {},
        "limits_override": {},
        "notes": "",
        "business_type": tenant.business_type if hasattr(tenant, 'business_type') else "retailer",
        "database_initialized": False,
        "created_at": now.isoformat()
    }
    
    await db.saas_tenants.insert_one(tenant_doc)
    await init_tenant_database(tenant_id)
    await db.saas_tenants.update_one({"id": tenant_id}, {"$set": {"database_initialized": True}})
    
    tenant_doc["plan_name"] = plan.get("name_ar", "")
    tenant_doc["agent_name"] = ""
    tenant_doc["stats"] = {"products": 0, "users": 1, "sales": 0}
    tenant_doc["database_initialized"] = True
    
    return TenantResponse(**{k: v for k, v in tenant_doc.items() if k not in ["_id", "password"]})

@router.put("/saas/tenants/{tenant_id}", response_model=TenantResponse)
async def update_tenant(tenant_id: str, updates: TenantUpdate, admin: dict = Depends(get_super_admin)):
    """Update a tenant"""
    tenant = await db.saas_tenants.find_one({"id": tenant_id})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.saas_tenants.update_one({"id": tenant_id}, {"$set": update_data})
    updated = await db.saas_tenants.find_one({"id": tenant_id}, {"_id": 0})
    
    plan = await db.saas_plans.find_one({"id": updated.get("plan_id")}, {"_id": 0, "name_ar": 1})
    updated["plan_name"] = plan.get("name_ar", "") if plan else ""
    updated["agent_name"] = ""
    updated["stats"] = {"products": 0, "users": 0, "sales": 0}
    
    return TenantResponse(**{k: v for k, v in updated.items() if k != "password"})

@router.delete("/saas/tenants/{tenant_id}")
async def delete_tenant(tenant_id: str, admin: dict = Depends(get_super_admin)):
    """Delete a tenant"""
    result = await db.saas_tenants.delete_one({"id": tenant_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return {"message": "Tenant deleted successfully"}

@router.post("/saas/tenants/{tenant_id}/toggle-status")
async def toggle_tenant_status(tenant_id: str, admin: dict = Depends(get_super_admin)):
    """Toggle tenant active status"""
    tenant = await db.saas_tenants.find_one({"id": tenant_id})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    new_status = not tenant.get("is_active", True)
    await db.saas_tenants.update_one({"id": tenant_id}, {"$set": {"is_active": new_status}})
    return {"is_active": new_status}

@router.post("/saas/tenants/{tenant_id}/extend-subscription")
async def extend_subscription(tenant_id: str, payment: SubscriptionPayment, admin: dict = Depends(get_super_admin)):
    """Extend tenant subscription"""
    tenant = await db.saas_tenants.find_one({"id": tenant_id})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    current_end = datetime.fromisoformat(tenant.get("subscription_ends_at", datetime.now(timezone.utc).isoformat()).replace('Z', '+00:00'))
    now = datetime.now(timezone.utc)
    start_date = max(current_end, now)
    
    if payment.subscription_type == "monthly":
        new_end = start_date + timedelta(days=30)
    elif payment.subscription_type == "6months":
        new_end = start_date + timedelta(days=180)
    else:
        new_end = start_date + timedelta(days=365)
    
    await db.saas_tenants.update_one({"id": tenant_id}, {"$set": {
        "subscription_type": payment.subscription_type,
        "subscription_ends_at": new_end.isoformat(),
        "is_active": True,
        "is_trial": False
    }})
    
    payment_doc = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "tenant_name": tenant.get("name", ""),
        "amount": payment.amount,
        "payment_method": payment.payment_method,
        "subscription_type": payment.subscription_type,
        "period_start": start_date.isoformat(),
        "period_end": new_end.isoformat(),
        "notes": payment.notes or "",
        "transaction_id": payment.transaction_id or "",
        "created_by": admin.get("id", ""),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.saas_payments.insert_one(payment_doc)
    
    return {"new_subscription_ends_at": new_end.isoformat()}

