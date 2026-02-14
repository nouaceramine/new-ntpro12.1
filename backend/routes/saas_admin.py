"""
SaaS Admin Routes - Multi-tenant management
All routes for super admin to manage tenants, plans, agents, and databases
Extracted from server.py for better code organization
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, Field
import uuid
import jwt
import bcrypt
import logging

logger = logging.getLogger(__name__)

# Import from main server for now - will be refactored later
import sys
sys.path.insert(0, '/app/backend')

from config.database import db, main_db, client, get_tenant_db, init_tenant_database

# JWT Settings (same as server.py)
import os
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
ALGORITHM = "HS256"

security = HTTPBearer()

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
    return PlanResponse(**plan_doc)

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
    
    # Cache agents for lookup
    agents_list = await db.saas_agents.find({}, {"_id": 0, "id": 1, "name": 1}).to_list(1000)
    agents_map = {a["id"]: a["name"] for a in agents_list}
    
    # Add plan names, agent names, and stats
    for tenant in tenants:
        plan = await db.saas_plans.find_one({"id": tenant.get("plan_id")}, {"_id": 0, "name": 1, "name_ar": 1})
        tenant["plan_name"] = plan.get("name_ar", "") if plan else ""
        
        # Add agent name
        agent_id = tenant.get("agent_id")
        tenant["agent_name"] = agents_map.get(agent_id, "") if agent_id else ""
        
        # Get tenant stats
        tenant_db = client[f"tenant_{tenant['id'].replace('-', '_')}"]
        products_count = await tenant_db.products.count_documents({})
        users_count = await tenant_db.users.count_documents({})
        sales_count = await tenant_db.sales.count_documents({})
        
        tenant["stats"] = {
            "products": products_count,
            "users": users_count,
            "sales": sales_count
        }
    
    return [TenantResponse(**t) for t in tenants]

@router.get("/saas/tenants/{tenant_id}", response_model=TenantResponse)
async def get_tenant(tenant_id: str, admin: dict = Depends(get_super_admin)):
    """Get a specific tenant"""
    tenant = await db.saas_tenants.find_one({"id": tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    plan = await db.saas_plans.find_one({"id": tenant.get("plan_id")}, {"_id": 0, "name_ar": 1})
    tenant["plan_name"] = plan.get("name_ar", "") if plan else ""
    
    # Get tenant stats
    tenant_db = client[f"tenant_{tenant['id'].replace('-', '_')}"]
    products_count = await tenant_db.products.count_documents({})
    users_count = await tenant_db.users.count_documents({})
    sales_count = await tenant_db.sales.count_documents({})
    
    tenant["stats"] = {
        "products": products_count,
        "users": users_count,
        "sales": sales_count
    }
    
    return TenantResponse(**tenant)

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
    
    # Calculate new end date
    current_end = datetime.fromisoformat(tenant.get("subscription_ends_at", datetime.now(timezone.utc).isoformat()).replace('Z', '+00:00'))
    now = datetime.now(timezone.utc)
    
    # Start from current end date or now, whichever is later
    start_date = max(current_end, now)
    
    if payment.subscription_type == "monthly":
        new_end = start_date + timedelta(days=30)
    elif payment.subscription_type == "6months":
        new_end = start_date + timedelta(days=180)
    else:  # yearly
        new_end = start_date + timedelta(days=365)
    
    # Update tenant
    await db.saas_tenants.update_one({"id": tenant_id}, {"$set": {
        "subscription_type": payment.subscription_type,
        "subscription_ends_at": new_end.isoformat(),
        "is_active": True,
        "is_trial": False
    }})
    
    # Record payment
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

# ============ STATS ROUTES ============

@router.get("/saas/stats")
async def get_saas_stats(admin: dict = Depends(get_super_admin)):
    """Get SaaS statistics overview"""
    now = datetime.now(timezone.utc)
    
    # Total tenants
    total_tenants = await db.saas_tenants.count_documents({})
    active_tenants = await db.saas_tenants.count_documents({"is_active": True})
    trial_tenants = await db.saas_tenants.count_documents({"is_trial": True})
    
    # Expiring soon (within 7 days)
    seven_days_later = now + timedelta(days=7)
    expiring_soon = await db.saas_tenants.count_documents({
        "is_active": True,
        "subscription_ends_at": {"$lte": seven_days_later.isoformat()}
    })
    
    # Revenue calculations
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    monthly_revenue_cursor = db.saas_payments.aggregate([
        {"$match": {"created_at": {"$gte": start_of_month.isoformat()}}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ])
    monthly_revenue_result = await monthly_revenue_cursor.to_list(1)
    monthly_revenue = monthly_revenue_result[0]["total"] if monthly_revenue_result else 0
    
    total_revenue_cursor = db.saas_payments.aggregate([
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ])
    total_revenue_result = await total_revenue_cursor.to_list(1)
    total_revenue = total_revenue_result[0]["total"] if total_revenue_result else 0
    
    # Plans distribution
    plans = await db.saas_plans.find({}, {"_id": 0, "id": 1, "name_ar": 1}).to_list(100)
    plans_distribution = {}
    for plan in plans:
        count = await db.saas_tenants.count_documents({"plan_id": plan["id"]})
        plans_distribution[plan.get("name_ar", plan["id"])] = count
    
    return {
        "total_tenants": total_tenants,
        "active_tenants": active_tenants,
        "trial_tenants": trial_tenants,
        "expiring_soon": expiring_soon,
        "monthly_revenue": monthly_revenue,
        "total_revenue": total_revenue,
        "plans_distribution": plans_distribution
    }

