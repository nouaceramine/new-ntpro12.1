"""
Customer Routes - All customer-related endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from models.schemas import CustomerCreate, CustomerResponse, CustomerUpdate
from utils.dependencies import get_current_user, get_admin_user
from config.database import db, get_tenant_db

router = APIRouter(prefix="/customers", tags=["Customers"])

@router.post("", response_model=CustomerResponse)
async def create_customer(customer: CustomerCreate, current_user: dict = Depends(get_current_user)):
    """Create a new customer"""
    tenant_id = current_user.get("tenant_id")
    target_db = get_tenant_db(tenant_id) if tenant_id else db
    
    customer_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    customer_doc = {
        "id": customer_id,
        **customer.model_dump(),
        "current_balance": 0,
        "total_purchases": 0,
        "loyalty_points": 0,
        "created_at": now
    }
    
    await target_db.customers.insert_one(customer_doc)
    return CustomerResponse(**customer_doc)

@router.get("", response_model=List[CustomerResponse])
async def get_customers(current_user: dict = Depends(get_current_user)):
    """Get all customers"""
    tenant_id = current_user.get("tenant_id")
    target_db = get_tenant_db(tenant_id) if tenant_id else db
    
    customers = await target_db.customers.find({}, {"_id": 0}).to_list(1000)
    return [CustomerResponse(**c) for c in customers]

@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: str, current_user: dict = Depends(get_current_user)):
    """Get customer by ID"""
    tenant_id = current_user.get("tenant_id")
    target_db = get_tenant_db(tenant_id) if tenant_id else db
    
    customer = await target_db.customers.find_one({"id": customer_id}, {"_id": 0})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return CustomerResponse(**customer)

@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(customer_id: str, customer: CustomerUpdate, current_user: dict = Depends(get_current_user)):
    """Update customer"""
    tenant_id = current_user.get("tenant_id")
    target_db = get_tenant_db(tenant_id) if tenant_id else db
    
    update_data = {k: v for k, v in customer.model_dump().items() if v is not None}
    if update_data:
        await target_db.customers.update_one({"id": customer_id}, {"$set": update_data})
    
    updated = await target_db.customers.find_one({"id": customer_id}, {"_id": 0})
    if not updated:
        raise HTTPException(status_code=404, detail="Customer not found")
    return CustomerResponse(**updated)

@router.delete("/{customer_id}")
async def delete_customer(customer_id: str, current_user: dict = Depends(get_admin_user)):
    """Delete customer (admin only)"""
    tenant_id = current_user.get("tenant_id")
    target_db = get_tenant_db(tenant_id) if tenant_id else db
    
    result = await target_db.customers.delete_one({"id": customer_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"message": "Customer deleted"}
