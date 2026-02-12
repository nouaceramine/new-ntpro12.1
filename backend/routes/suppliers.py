"""
Supplier Routes - All supplier-related endpoints
Tenant-specific routes using require_tenant for RBAC
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from datetime import datetime, timezone
import uuid

from models.schemas import SupplierCreate, SupplierResponse, SupplierUpdate
from utils.dependencies import get_current_user, get_admin_user, require_tenant, get_tenant_admin
from config.database import db, get_tenant_db

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])

@router.post("", response_model=SupplierResponse)
async def create_supplier(supplier: SupplierCreate, current_user: dict = Depends(get_current_user)):
    """Create a new supplier"""
    tenant_id = current_user.get("tenant_id")
    target_db = get_tenant_db(tenant_id) if tenant_id else db
    
    supplier_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    supplier_doc = {
        "id": supplier_id,
        **supplier.model_dump(),
        "current_balance": 0,
        "total_purchases": 0,
        "advance_balance": 0,
        "created_at": now
    }
    
    await target_db.suppliers.insert_one(supplier_doc)
    return SupplierResponse(**supplier_doc)

@router.get("", response_model=List[SupplierResponse])
async def get_suppliers(current_user: dict = Depends(get_current_user)):
    """Get all suppliers"""
    tenant_id = current_user.get("tenant_id")
    target_db = get_tenant_db(tenant_id) if tenant_id else db
    
    suppliers = await target_db.suppliers.find({}, {"_id": 0}).to_list(1000)
    return [SupplierResponse(**s) for s in suppliers]

@router.get("/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(supplier_id: str, current_user: dict = Depends(get_current_user)):
    """Get supplier by ID"""
    tenant_id = current_user.get("tenant_id")
    target_db = get_tenant_db(tenant_id) if tenant_id else db
    
    supplier = await target_db.suppliers.find_one({"id": supplier_id}, {"_id": 0})
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return SupplierResponse(**supplier)

@router.delete("/{supplier_id}")
async def delete_supplier(supplier_id: str, current_user: dict = Depends(get_admin_user)):
    """Delete supplier (admin only)"""
    tenant_id = current_user.get("tenant_id")
    target_db = get_tenant_db(tenant_id) if tenant_id else db
    
    result = await target_db.suppliers.delete_one({"id": supplier_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return {"message": "Supplier deleted"}
