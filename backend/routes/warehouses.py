"""
Warehouse Routes - Inventory and warehouse management
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from datetime import datetime, timezone
import uuid

from models.schemas import WarehouseCreate, WarehouseResponse, WarehouseUpdate
from utils.dependencies import get_current_user, get_admin_user
from config.database import db, get_tenant_db

router = APIRouter(prefix="/warehouses", tags=["Warehouses"])

@router.post("", response_model=WarehouseResponse)
async def create_warehouse(warehouse: WarehouseCreate, current_user: dict = Depends(get_admin_user)):
    """Create a new warehouse"""
    tenant_id = current_user.get("tenant_id")
    target_db = get_tenant_db(tenant_id) if tenant_id else db
    
    warehouse_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    warehouse_doc = {
        "id": warehouse_id,
        **warehouse.model_dump(),
        "created_at": now
    }
    
    await target_db.warehouses.insert_one(warehouse_doc)
    return WarehouseResponse(**warehouse_doc, total_products=0, total_value=0)

@router.get("", response_model=List[WarehouseResponse])
async def get_warehouses(current_user: dict = Depends(get_current_user)):
    """Get all warehouses with stats"""
    tenant_id = current_user.get("tenant_id")
    target_db = get_tenant_db(tenant_id) if tenant_id else db
    
    warehouses = await target_db.warehouses.find({}, {"_id": 0}).to_list(100)
    result = []
    
    for w in warehouses:
        # Calculate stats
        products = await target_db.products.find(
            {"warehouse_id": w["id"]}, 
            {"quantity": 1, "retail_price": 1}
        ).to_list(10000)
        
        total_products = len(products)
        total_value = sum(p.get("quantity", 0) * p.get("retail_price", 0) for p in products)
        
        result.append(WarehouseResponse(
            **w,
            total_products=total_products,
            total_value=total_value
        ))
    
    return result

@router.delete("/{warehouse_id}")
async def delete_warehouse(warehouse_id: str, current_user: dict = Depends(get_admin_user)):
    """Delete warehouse"""
    tenant_id = current_user.get("tenant_id")
    target_db = get_tenant_db(tenant_id) if tenant_id else db
    
    # Check if main warehouse
    warehouse = await target_db.warehouses.find_one({"id": warehouse_id})
    if warehouse and warehouse.get("is_main"):
        raise HTTPException(status_code=400, detail="Cannot delete main warehouse")
    
    result = await target_db.warehouses.delete_one({"id": warehouse_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    return {"message": "Warehouse deleted"}
