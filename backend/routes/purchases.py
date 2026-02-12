"""
Purchase Routes - All purchase-related endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from datetime import datetime, timezone
import uuid

from models.schemas import PurchaseCreate, PurchaseResponse
from utils.dependencies import get_current_user
from config.database import db, get_tenant_db
from services.code_generator import generate_purchase_code

router = APIRouter(prefix="/purchases", tags=["Purchases"])

@router.post("", response_model=PurchaseResponse)
async def create_purchase(purchase: PurchaseCreate, current_user: dict = Depends(get_current_user)):
    """Create a new purchase"""
    tenant_id = current_user.get("tenant_id")
    target_db = get_tenant_db(tenant_id) if tenant_id else db
    
    purchase_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    # Generate purchase code
    purchase_code = await generate_purchase_code(target_db)
    
    # Calculate final total
    final_total = purchase.total - purchase.discount + purchase.tax
    
    purchase_doc = {
        "id": purchase_id,
        "purchase_code": purchase_code,
        "items": [item.model_dump() for item in purchase.items],
        "total": purchase.total,
        "discount": purchase.discount,
        "tax": purchase.tax,
        "final_total": final_total,
        "payment_type": purchase.payment_type,
        "paid_amount": purchase.paid_amount,
        "remaining": purchase.remaining,
        "supplier_id": purchase.supplier_id,
        "supplier_name": purchase.supplier_name,
        "notes": purchase.notes or "",
        "warehouse_id": purchase.warehouse_id or "main",
        "user_id": current_user["id"],
        "user_name": current_user.get("name", ""),
        "created_at": now
    }
    
    await target_db.purchases.insert_one(purchase_doc)
    
    # Update stock for each item
    for item in purchase.items:
        await target_db.products.update_one(
            {"id": item.product_id},
            {"$inc": {"quantity": item.quantity}}
        )
    
    # Update supplier balance if credit purchase
    if purchase.remaining > 0 and purchase.supplier_id:
        await target_db.suppliers.update_one(
            {"id": purchase.supplier_id},
            {"$inc": {"current_balance": purchase.remaining}}
        )
    
    # Update cash box
    if purchase.paid_amount > 0:
        box_id = "bank" if purchase.payment_type == "transfer" else "cash"
        await target_db.cash_boxes.update_one(
            {"id": box_id},
            {"$inc": {"balance": -purchase.paid_amount}}
        )
    
    return PurchaseResponse(**purchase_doc)

@router.get("", response_model=List[PurchaseResponse])
async def get_purchases(
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """Get purchases list"""
    tenant_id = current_user.get("tenant_id")
    target_db = get_tenant_db(tenant_id) if tenant_id else db
    
    purchases = await target_db.purchases.find({}, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    return [PurchaseResponse(**p) for p in purchases]
