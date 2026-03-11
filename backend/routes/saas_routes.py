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

# JWT Settings - Use same key as main server
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'nt_commerce_super_secure_jwt_secret_key_2024_v3_hardened')
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


# ============ MONITORING & STATS ROUTES ============

@router.get("/saas/monitoring")
async def get_monitoring_data(admin: dict = Depends(get_super_admin)):
    """Get monitoring data for all tenants"""
    tenants = await db.saas_tenants.find({}, {"_id": 0}).to_list(1000)
    monitoring_data = []
    
    for tenant in tenants:
        tenant_db = client[f"tenant_{tenant['id'].replace('-', '_')}"]
        products_count = await tenant_db.products.count_documents({})
        customers_count = await tenant_db.customers.count_documents({})
        sales_count = await tenant_db.sales.count_documents({})
        
        monitoring_data.append({
            "tenant_id": tenant["id"],
            "name": tenant.get("name", ""),
            "email": tenant.get("email", ""),
            "company_name": tenant.get("company_name", ""),
            "is_active": tenant.get("is_active", True),
            "products_count": products_count,
            "customers_count": customers_count,
            "sales_count": sales_count,
            "subscription_ends_at": tenant.get("subscription_ends_at", ""),
            "created_at": tenant.get("created_at", "")
        })
    
    total_products = sum(t["products_count"] for t in monitoring_data)
    total_customers = sum(t["customers_count"] for t in monitoring_data)
    total_sales = sum(t["sales_count"] for t in monitoring_data)
    
    return {
        "tenants": monitoring_data,
        "totals": {
            "products": total_products,
            "customers": total_customers,
            "sales": total_sales
        }
    }

@router.get("/saas/payments", response_model=List[SubscriptionPaymentResponse])
async def get_payments(
    limit: int = 100,
    skip: int = 0,
    tenant_id: Optional[str] = None,
    admin: dict = Depends(get_super_admin)
):
    """Get subscription payments"""
    query = {"tenant_id": tenant_id} if tenant_id else {}
    payments = await db.saas_payments.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    return [SubscriptionPaymentResponse(**p) for p in payments]

@router.get("/saas/finance-reports")
async def get_finance_reports(admin: dict = Depends(get_super_admin)):
    """Get financial reports"""
    now = datetime.now(timezone.utc)
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    start_of_year = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    
    monthly_revenue = 0
    yearly_revenue = 0
    
    async for payment in db.saas_payments.find({"created_at": {"$gte": start_of_month.isoformat()}}, {"_id": 0}):
        monthly_revenue += payment.get("amount", 0)
    
    async for payment in db.saas_payments.find({"created_at": {"$gte": start_of_year.isoformat()}}, {"_id": 0}):
        yearly_revenue += payment.get("amount", 0)
    
    return {
        "monthly_revenue": monthly_revenue,
        "yearly_revenue": yearly_revenue,
        "currency": "دج"
    }

@router.get("/saas/stats")
async def get_saas_stats(admin: dict = Depends(get_super_admin)):
    """Get SaaS statistics"""
    now = datetime.now(timezone.utc)
    
    total_tenants = await db.saas_tenants.count_documents({})
    active_tenants = await db.saas_tenants.count_documents({"is_active": True})
    trial_tenants = await db.saas_tenants.count_documents({"is_trial": True})
    
    seven_days_later = now + timedelta(days=7)
    expiring_soon = await db.saas_tenants.count_documents({
        "is_active": True,
        "subscription_ends_at": {"$lte": seven_days_later.isoformat()}
    })
    
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

@router.get("/saas/stats-extended")
async def get_stats_extended(admin: dict = Depends(get_super_admin)):
    """Get extended statistics"""
    now = datetime.now(timezone.utc)
    
    total_tenants = await db.saas_tenants.count_documents({})
    active_tenants = await db.saas_tenants.count_documents({"is_active": True})
    total_agents = await db.saas_agents.count_documents({})
    
    seven_days_later = now + timedelta(days=7)
    expiring_soon = await db.saas_tenants.count_documents({
        "is_active": True,
        "subscription_ends_at": {"$lte": seven_days_later.isoformat()}
    })
    
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    revenue_cursor = db.saas_payments.aggregate([
        {"$match": {"created_at": {"$gte": start_of_month.isoformat()}}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ])
    revenue_result = await revenue_cursor.to_list(1)
    monthly_revenue = revenue_result[0]["total"] if revenue_result else 0
    
    return {
        "total_tenants": total_tenants,
        "active_tenants": active_tenants,
        "total_agents": total_agents,
        "expiring_soon": expiring_soon,
        "monthly_revenue": monthly_revenue
    }


# ============ AGENTS/RESELLERS ROUTES ============

@router.get("/saas/agents", response_model=List[AgentResponse])
async def get_agents(admin: dict = Depends(get_super_admin)):
    """Get all agents"""
    agents = await db.saas_agents.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    result = []
    for agent in agents:
        tenants_count = await db.saas_tenants.count_documents({"agent_id": agent["id"]})
        agent_data = {k: v for k, v in agent.items() if k != "password"}
        agent_data["tenants_count"] = tenants_count
        result.append(AgentResponse(**agent_data))
    return result

@router.get("/saas/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str, admin: dict = Depends(get_super_admin)):
    """Get a specific agent"""
    agent = await db.saas_agents.find_one({"id": agent_id}, {"_id": 0})
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    tenants_count = await db.saas_tenants.count_documents({"agent_id": agent_id})
    agent_data = {k: v for k, v in agent.items() if k != "password"}
    agent_data["tenants_count"] = tenants_count
    return AgentResponse(**agent_data)

@router.post("/saas/agents", response_model=AgentResponse)
async def create_agent(agent: AgentCreate, admin: dict = Depends(get_super_admin)):
    """Create a new agent"""
    existing = await db.saas_agents.find_one({"email": agent.email})
    if existing:
        raise HTTPException(status_code=400, detail="البريد الإلكتروني مستخدم بالفعل")
    
    hashed_password = bcrypt.hashpw(agent.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    agent_doc = {
        "id": str(uuid.uuid4()),
        "name": agent.name,
        "email": agent.email,
        "password": hashed_password,
        "phone": agent.phone or "",
        "commission_rate": agent.commission_rate,
        "total_earnings": 0,
        "pending_earnings": 0,
        "paid_earnings": 0,
        "notes": agent.notes or "",
        "is_active": agent.is_active,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.saas_agents.insert_one(agent_doc)
    return AgentResponse(**{k: v for k, v in agent_doc.items() if k not in ["_id", "password"]}, tenants_count=0)

@router.put("/saas/agents/{agent_id}", response_model=AgentResponse)
async def update_agent(agent_id: str, updates: AgentUpdate, admin: dict = Depends(get_super_admin)):
    """Update an agent"""
    agent = await db.saas_agents.find_one({"id": agent_id})
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.saas_agents.update_one({"id": agent_id}, {"$set": update_data})
    updated = await db.saas_agents.find_one({"id": agent_id}, {"_id": 0})
    tenants_count = await db.saas_tenants.count_documents({"agent_id": agent_id})
    
    return AgentResponse(**{k: v for k, v in updated.items() if k != "password"}, tenants_count=tenants_count)

@router.delete("/saas/agents/{agent_id}")
async def delete_agent(agent_id: str, admin: dict = Depends(get_super_admin)):
    """Delete an agent"""
    result = await db.saas_agents.delete_one({"id": agent_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"message": "Agent deleted successfully"}

@router.get("/saas/agents/{agent_id}/transactions")
async def get_agent_transactions(agent_id: str, admin: dict = Depends(get_super_admin)):
    """Get agent transactions"""
    transactions = await db.saas_agent_transactions.find({"agent_id": agent_id}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return transactions

@router.post("/saas/agents/{agent_id}/transactions", response_model=AgentTransactionResponse)
async def create_agent_transaction(agent_id: str, transaction: AgentTransactionCreate, admin: dict = Depends(get_super_admin)):
    """Create agent transaction"""
    agent = await db.saas_agents.find_one({"id": agent_id})
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    tenant_name = ""
    if transaction.tenant_id:
        tenant = await db.saas_tenants.find_one({"id": transaction.tenant_id}, {"_id": 0, "name": 1})
        tenant_name = tenant.get("name", "") if tenant else ""
    
    transaction_doc = {
        "id": str(uuid.uuid4()),
        "agent_id": agent_id,
        "type": transaction.type,
        "amount": transaction.amount,
        "tenant_id": transaction.tenant_id,
        "tenant_name": tenant_name,
        "notes": transaction.notes or "",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.saas_agent_transactions.insert_one(transaction_doc)
    
    if transaction.type == "commission":
        await db.saas_agents.update_one({"id": agent_id}, {
            "$inc": {"total_earnings": transaction.amount, "pending_earnings": transaction.amount}
        })
    elif transaction.type == "payout":
        await db.saas_agents.update_one({"id": agent_id}, {
            "$inc": {"pending_earnings": -transaction.amount, "paid_earnings": transaction.amount}
        })
    
    return AgentTransactionResponse(**{k: v for k, v in transaction_doc.items() if k != "_id"})

@router.get("/saas/agents/{agent_id}/tenants")
async def get_agent_tenants(agent_id: str, admin: dict = Depends(get_super_admin)):
    """Get tenants under an agent"""
    tenants = await db.saas_tenants.find({"agent_id": agent_id}, {"_id": 0}).to_list(1000)
    return tenants

@router.post("/saas/agent-login")
async def agent_login(login_data: AgentLoginRequest):
    """Agent login"""
    agent = await db.saas_agents.find_one({"email": login_data.email})
    if not agent:
        raise HTTPException(status_code=401, detail="بيانات الدخول غير صحيحة")
    
    if not bcrypt.checkpw(login_data.password.encode('utf-8'), agent["password"].encode('utf-8')):
        raise HTTPException(status_code=401, detail="بيانات الدخول غير صحيحة")
    
    if not agent.get("is_active", True):
        raise HTTPException(status_code=403, detail="الحساب معطل")
    
    access_token = create_access_token({
        "sub": agent["id"],
        "email": agent["email"],
        "role": "agent",
        "type": "agent"
    })
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {k: v for k, v in agent.items() if k not in ["_id", "password"]}
    }


# ============ TENANT REGISTRATION (Public) ============

@router.post("/saas/register")
async def register_tenant(tenant: TenantCreate):
    """Public tenant registration"""
    existing = await db.saas_tenants.find_one({"email": tenant.email})
    if existing:
        raise HTTPException(status_code=400, detail="البريد الإلكتروني مستخدم بالفعل")
    
    plan = await db.saas_plans.find_one({"id": tenant.plan_id}, {"_id": 0})
    if not plan:
        raise HTTPException(status_code=404, detail="الخطة غير موجودة")
    
    now = datetime.now(timezone.utc)
    trial_ends_at = now + timedelta(days=14)
    
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
        "agent_id": tenant.agent_id if hasattr(tenant, 'agent_id') and tenant.agent_id else None,
        "is_active": True,
        "is_trial": True,
        "trial_ends_at": trial_ends_at.isoformat(),
        "subscription_type": "monthly",
        "subscription_starts_at": now.isoformat(),
        "subscription_ends_at": trial_ends_at.isoformat(),
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
    
    if tenant_doc.get("agent_id"):
        agent = await db.saas_agents.find_one({"id": tenant_doc["agent_id"]})
        if agent:
            commission = plan.get("monthly_price", 0) * (agent.get("commission_rate", 10) / 100)
            if commission > 0:
                transaction_doc = {
                    "id": str(uuid.uuid4()),
                    "agent_id": agent["id"],
                    "type": "commission",
                    "amount": commission,
                    "tenant_id": tenant_id,
                    "tenant_name": tenant.name,
                    "notes": f"عمولة تسجيل مشترك جديد: {tenant.name}",
                    "created_at": now.isoformat()
                }
                await db.saas_agent_transactions.insert_one(transaction_doc)
                await db.saas_agents.update_one({"id": agent["id"]}, {
                    "$inc": {"total_earnings": commission, "pending_earnings": commission}
                })
    
    access_token = create_access_token({
        "sub": tenant_id,
        "email": tenant.email,
        "role": "admin",
        "type": "tenant",
        "tenant_id": tenant_id
    })
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "tenant_id": tenant_id,
        "message": "تم إنشاء حسابك بنجاح! لديك 14 يوماً تجريبية.",
        "trial_ends_at": trial_ends_at.isoformat()
    }

@router.post("/saas/tenant-login")
async def tenant_login(login_data: AgentLoginRequest):
    """Tenant login"""
    tenant = await db.saas_tenants.find_one({"email": login_data.email})
    if not tenant:
        raise HTTPException(status_code=401, detail="بيانات الدخول غير صحيحة")
    
    if not bcrypt.checkpw(login_data.password.encode('utf-8'), tenant["password"].encode('utf-8')):
        raise HTTPException(status_code=401, detail="بيانات الدخول غير صحيحة")
    
    if not tenant.get("is_active", True):
        raise HTTPException(status_code=403, detail="الحساب معطل")
    
    access_token = create_access_token({
        "sub": tenant["id"],
        "email": tenant["email"],
        "role": "admin",
        "type": "tenant",
        "tenant_id": tenant["id"]
    })
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "tenant_id": tenant["id"],
        "user": {
            "id": tenant["id"],
            "email": tenant["email"],
            "name": tenant.get("name", ""),
            "role": "admin",
            "tenant_id": tenant["id"],
            "company_name": tenant.get("company_name", "")
        }
    }


# ============ DATABASE MANAGEMENT ROUTES ============

@router.get("/saas/databases")
async def get_databases(admin: dict = Depends(get_super_admin)):
    """Get all tenant databases"""
    tenants = await db.saas_tenants.find({}, {"_id": 0}).to_list(1000)
    databases = []
    
    for tenant in tenants:
        db_name = f"tenant_{tenant['id'].replace('-', '_')}"
        tenant_db = client[db_name]
        
        collections = await tenant_db.list_collection_names()
        total_docs = 0
        for coll in collections:
            count = await tenant_db[coll].count_documents({})
            total_docs += count
        
        databases.append({
            "id": tenant["id"],
            "name": tenant.get("name", ""),
            "email": tenant.get("email", ""),
            "company_name": tenant.get("company_name", ""),
            "database_name": db_name,
            "collections_count": len(collections),
            "documents_count": total_docs,
            "is_active": tenant.get("is_active", True),
            "is_frozen": tenant.get("is_frozen", False),
            "created_at": tenant.get("created_at", "")
        })
    
    return databases

@router.get("/saas/databases/stats")
async def get_databases_stats(admin: dict = Depends(get_super_admin)):
    """Get database statistics"""
    tenants = await db.saas_tenants.find({}, {"_id": 0}).to_list(1000)
    
    total_databases = len(tenants)
    total_collections = 0
    total_documents = 0
    
    for tenant in tenants:
        db_name = f"tenant_{tenant['id'].replace('-', '_')}"
        tenant_db = client[db_name]
        
        collections = await tenant_db.list_collection_names()
        total_collections += len(collections)
        
        for coll in collections:
            count = await tenant_db[coll].count_documents({})
            total_documents += count
    
    return {
        "total_databases": total_databases,
        "total_collections": total_collections,
        "total_documents": total_documents
    }

@router.get("/saas/databases/logs")
async def get_databases_logs(admin: dict = Depends(get_super_admin)):
    """Get database logs"""
    return []

@router.get("/saas/databases/backups")
async def get_databases_backups(admin: dict = Depends(get_super_admin)):
    """Get database backups"""
    return []

@router.post("/saas/databases/{db_id}/backup")
async def create_database_backup(db_id: str, admin: dict = Depends(get_super_admin)):
    """Create database backup"""
    tenant = await db.saas_tenants.find_one({"id": db_id})
    if not tenant:
        raise HTTPException(status_code=404, detail="Database not found")
    
    db_name = f"tenant_{db_id.replace('-', '_')}"
    tenant_db = client[db_name]
    
    backup_data = {}
    collections = await tenant_db.list_collection_names()
    
    for coll in collections:
        docs = await tenant_db[coll].find({}, {"_id": 0}).to_list(10000)
        backup_data[coll] = docs
    
    backup_doc = {
        "id": str(uuid.uuid4()),
        "tenant_id": db_id,
        "database_name": db_name,
        "data": backup_data,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": admin.get("id", "")
    }
    
    await db.database_backups.insert_one(backup_doc)
    
    return {"message": "Backup created successfully", "backup_id": backup_doc["id"]}

@router.post("/saas/databases/{db_id}/freeze")
async def freeze_database(db_id: str, admin: dict = Depends(get_super_admin)):
    """Freeze/unfreeze database"""
    tenant = await db.saas_tenants.find_one({"id": db_id})
    if not tenant:
        raise HTTPException(status_code=404, detail="Database not found")
    
    new_status = not tenant.get("is_frozen", False)
    await db.saas_tenants.update_one({"id": db_id}, {"$set": {"is_frozen": new_status}})
    
    return {"is_frozen": new_status}

@router.delete("/saas/databases/{db_id}")
async def delete_database(db_id: str, admin: dict = Depends(get_super_admin)):
    """Delete tenant database"""
    tenant = await db.saas_tenants.find_one({"id": db_id})
    if not tenant:
        raise HTTPException(status_code=404, detail="Database not found")
    
    db_name = f"tenant_{db_id.replace('-', '_')}"
    await client.drop_database(db_name)
    await db.saas_tenants.delete_one({"id": db_id})
    
    return {"message": "Database deleted successfully"}

@router.get("/saas/databases/{db_id}/export")
async def export_database(db_id: str, admin: dict = Depends(get_super_admin)):
    """Export database as JSON"""
    tenant = await db.saas_tenants.find_one({"id": db_id})
    if not tenant:
        raise HTTPException(status_code=404, detail="Database not found")
    
    db_name = f"tenant_{db_id.replace('-', '_')}"
    tenant_db = client[db_name]
    
    export_data = {"tenant_id": db_id, "database_name": db_name, "collections": {}}
    collections = await tenant_db.list_collection_names()
    
    for coll in collections:
        docs = await tenant_db[coll].find({}, {"_id": 0}).to_list(10000)
        export_data["collections"][coll] = docs
    
    json_data = json.dumps(export_data, ensure_ascii=False, indent=2, default=str)
    
    return StreamingResponse(
        io.BytesIO(json_data.encode('utf-8')),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={db_name}_export.json"}
    )

@router.post("/saas/databases/{db_id}/schedule")
async def schedule_database_task(db_id: str, task: dict = Body(...), admin: dict = Depends(get_super_admin)):
    """Schedule database maintenance task"""
    tenant = await db.saas_tenants.find_one({"id": db_id})
    if not tenant:
        raise HTTPException(status_code=404, detail="Database not found")
    
    return {"message": "Task scheduled", "task": task}

