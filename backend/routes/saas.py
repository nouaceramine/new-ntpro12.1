"""
SaaS Routes - Multi-tenant management endpoints
Super Admin only routes for managing tenants, plans, and agents
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from datetime import datetime, timezone, timedelta
import uuid
import bcrypt

from models.schemas import (
    TenantCreate, TenantResponse, TenantUpdate,
    AgentCreate, AgentResponse, AgentUpdate,
    PlanCreate, PlanResponse, PlanUpdate
)
from utils.dependencies import get_current_user, get_super_admin
from utils.auth import hash_password
from config.database import db, main_db, get_tenant_db, init_tenant_database, client

router = APIRouter(prefix="/saas", tags=["SaaS"])

# ============ PLANS ============

@router.get("/plans", response_model=List[PlanResponse])
async def get_plans():
    """Get all active plans"""
    plans = await db.saas_plans.find({"is_active": True}, {"_id": 0}).to_list(100)
    return [PlanResponse(**p) for p in plans]

@router.post("/plans", response_model=PlanResponse)
async def create_plan(plan: PlanCreate, admin: dict = Depends(get_super_admin)):
    """Create a new plan (super admin only)"""
    plan_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    plan_doc = {
        "id": plan_id,
        **plan.model_dump(),
        "created_at": now
    }
    
    await db.saas_plans.insert_one(plan_doc)
    return PlanResponse(**plan_doc)

# ============ TENANTS ============

@router.get("/tenants", response_model=List[TenantResponse])
async def get_tenants(admin: dict = Depends(get_super_admin)):
    """Get all tenants (super admin only)"""
    tenants = await db.saas_tenants.find({}, {"_id": 0, "password": 0}).to_list(1000)
    
    result = []
    for t in tenants:
        # Get plan name
        if t.get("plan_id"):
            plan = await db.saas_plans.find_one({"id": t["plan_id"]}, {"name_ar": 1})
            t["plan_name"] = plan.get("name_ar", "") if plan else ""
        
        # Get agent name
        if t.get("agent_id"):
            agent = await db.saas_agents.find_one({"id": t["agent_id"]}, {"name": 1})
            t["agent_name"] = agent.get("name", "") if agent else ""
        
        result.append(TenantResponse(**t))
    
    return result

@router.post("/tenants", response_model=TenantResponse)
async def create_tenant(tenant: TenantCreate, admin: dict = Depends(get_super_admin)):
    """Create a new tenant (super admin only)"""
    # Check email uniqueness
    existing = await db.saas_tenants.find_one({"email": tenant.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Verify plan exists
    plan = await db.saas_plans.find_one({"id": tenant.plan_id})
    if not plan:
        raise HTTPException(status_code=400, detail="Plan not found")
    
    tenant_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    
    # Calculate subscription end date
    if tenant.subscription_type == "monthly":
        ends_at = now + timedelta(days=30)
    elif tenant.subscription_type == "6months":
        ends_at = now + timedelta(days=180)
    else:  # yearly
        ends_at = now + timedelta(days=365)
    
    hashed_password = hash_password(tenant.password)
    
    tenant_doc = {
        "id": tenant_id,
        "name": tenant.name,
        "email": tenant.email,
        "phone": tenant.phone or "",
        "company_name": tenant.company_name or "",
        "password": hashed_password,
        "plan_id": tenant.plan_id,
        "agent_id": tenant.agent_id,
        "is_active": True,
        "is_trial": False,
        "subscription_type": tenant.subscription_type,
        "subscription_starts_at": now.isoformat(),
        "subscription_ends_at": ends_at.isoformat(),
        "features_override": {},
        "limits_override": {},
        "notes": tenant.notes or "",
        "business_type": tenant.business_type or "retailer",
        "database_name": f"tenant_{tenant_id.replace('-', '_')}",
        "database_initialized": True,
        "first_login_at": now.isoformat(),
        "created_at": now.isoformat()
    }
    
    await db.saas_tenants.insert_one(tenant_doc)
    
    # Initialize tenant database
    await init_tenant_database(tenant_id)
    
    # Create admin user in tenant database
    tenant_db = get_tenant_db(tenant_id)
    admin_user = {
        "id": str(uuid.uuid4()),
        "name": tenant.name,
        "email": tenant.email,
        "password": hashed_password,
        "role": "admin",
        "permissions": {},
        "created_at": now.isoformat()
    }
    await tenant_db.users.insert_one(admin_user)
    
    return TenantResponse(**{k: v for k, v in tenant_doc.items() if k != "password"})

# ============ AGENTS ============

@router.get("/agents", response_model=List[AgentResponse])
async def get_agents(admin: dict = Depends(get_super_admin)):
    """Get all agents"""
    agents = await db.saas_agents.find({}, {"_id": 0, "password": 0}).to_list(100)
    
    result = []
    for a in agents:
        # Count tenants
        tenants_count = await db.saas_tenants.count_documents({"agent_id": a["id"]})
        a["tenants_count"] = tenants_count
        result.append(AgentResponse(**a))
    
    return result

@router.post("/agents", response_model=AgentResponse)
async def create_agent(agent: AgentCreate, admin: dict = Depends(get_super_admin)):
    """Create a new agent"""
    existing = await db.saas_agents.find_one({"email": agent.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    agent_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    agent_doc = {
        "id": agent_id,
        **agent.model_dump(exclude={"password"}),
        "password": hash_password(agent.password),
        "is_active": True,
        "current_balance": 0,
        "total_earnings": 0,
        "created_at": now
    }
    
    await db.saas_agents.insert_one(agent_doc)
    return AgentResponse(**{k: v for k, v in agent_doc.items() if k != "password"}, tenants_count=0)
