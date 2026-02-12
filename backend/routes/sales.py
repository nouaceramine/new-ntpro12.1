"""
Sales Routes - All sales-related endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from models.schemas import SaleCreate, SaleResponse
from utils.dependencies import get_current_user
from config.database import db, get_tenant_db
from services.code_generator import generate_sale_code

router = APIRouter(prefix="/sales", tags=["Sales"])

@router.post("", response_model=SaleResponse)
async def create_sale(sale: SaleCreate, current_user: dict = Depends(get_current_user)):
    """Create a new sale"""
    tenant_id = current_user.get("tenant_id")
    target_db = get_tenant_db(tenant_id) if tenant_id else db
    
    sale_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    # Generate sale code
    sale_code = await generate_sale_code(target_db)
    
    # Calculate final total
    final_total = sale.total - sale.discount + sale.tax
    
    sale_doc = {
        "id": sale_id,
        "sale_code": sale_code,
        "items": [item.model_dump() for item in sale.items],
        "total": sale.total,
        "discount": sale.discount,
        "tax": sale.tax,
        "final_total": final_total,
        "payment_type": sale.payment_type,
        "paid_amount": sale.paid_amount,
        "remaining": sale.remaining,
        "customer_id": sale.customer_id,
        "customer_name": sale.customer_name,
        "notes": sale.notes or "",
        "warehouse_id": sale.warehouse_id or "main",
        "user_id": current_user["id"],
        "user_name": current_user.get("name", ""),
        "created_at": now
    }
    
    await target_db.sales.insert_one(sale_doc)
    
    # Update stock for each item
    for item in sale.items:
        await target_db.products.update_one(
            {"id": item.product_id},
            {"$inc": {"quantity": -item.quantity}}
        )
    
    # Update customer balance if credit sale
    if sale.remaining > 0 and sale.customer_id:
        await target_db.customers.update_one(
            {"id": sale.customer_id},
            {
                "$inc": {
                    "current_balance": sale.remaining,
                    "total_purchases": final_total
                },
                "$set": {"last_purchase": now}
            }
        )
    
    # Update cash box
    if sale.paid_amount > 0:
        box_id = "bank" if sale.payment_type == "card" else "cash"
        await target_db.cash_boxes.update_one(
            {"id": box_id},
            {"$inc": {"balance": sale.paid_amount}}
        )
    
    return SaleResponse(**sale_doc)

@router.get("", response_model=List[SaleResponse])
async def get_sales(
    limit: int = 100,
    skip: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """Get sales list"""
    tenant_id = current_user.get("tenant_id")
    target_db = get_tenant_db(tenant_id) if tenant_id else db
    
    sales = await target_db.sales.find({}, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    return [SaleResponse(**s) for s in sales]

@router.get("/{sale_id}", response_model=SaleResponse)
async def get_sale(sale_id: str, current_user: dict = Depends(get_current_user)):
    """Get sale by ID"""
    tenant_id = current_user.get("tenant_id")
    target_db = get_tenant_db(tenant_id) if tenant_id else db
    
    sale = await target_db.sales.find_one({"id": sale_id}, {"_id": 0})
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    return SaleResponse(**sale)
