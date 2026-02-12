"""
Reports Routes - Analytics and reporting endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime, timezone, timedelta

from utils.dependencies import get_current_user
from config.database import db, get_tenant_db

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/dashboard")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    """Get dashboard statistics"""
    tenant_id = current_user.get("tenant_id")
    target_db = get_tenant_db(tenant_id) if tenant_id else db
    
    # Today's date range
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_str = today.isoformat()
    
    # Get counts
    products_count = await target_db.products.count_documents({})
    customers_count = await target_db.customers.count_documents({})
    suppliers_count = await target_db.suppliers.count_documents({})
    
    # Today's sales
    today_sales = await target_db.sales.find(
        {"created_at": {"$gte": today_str}},
        {"final_total": 1}
    ).to_list(10000)
    today_revenue = sum(s.get("final_total", 0) for s in today_sales)
    
    # Low stock products
    low_stock = await target_db.products.count_documents({
        "$expr": {"$lte": ["$quantity", "$min_stock"]}
    })
    
    # Cash box balances
    cash_boxes = await target_db.cash_boxes.find({}, {"_id": 0}).to_list(10)
    total_cash = sum(box.get("balance", 0) for box in cash_boxes)
    
    return {
        "products_count": products_count,
        "customers_count": customers_count,
        "suppliers_count": suppliers_count,
        "today_sales_count": len(today_sales),
        "today_revenue": today_revenue,
        "low_stock_count": low_stock,
        "total_cash": total_cash,
        "cash_boxes": cash_boxes
    }

@router.get("/sales-summary")
async def get_sales_summary(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get sales summary for date range"""
    tenant_id = current_user.get("tenant_id")
    target_db = get_tenant_db(tenant_id) if tenant_id else db
    
    # Default to last 30 days
    if not end_date:
        end_date = datetime.now(timezone.utc).isoformat()
    if not start_date:
        start = datetime.now(timezone.utc) - timedelta(days=30)
        start_date = start.isoformat()
    
    query = {"created_at": {"$gte": start_date, "$lte": end_date}}
    
    sales = await target_db.sales.find(query, {"_id": 0}).to_list(10000)
    
    total_revenue = sum(s.get("final_total", 0) for s in sales)
    total_profit = sum(
        sum(item.get("total", 0) - (item.get("purchase_price", 0) * item.get("quantity", 0)) 
            for item in s.get("items", []))
        for s in sales
    )
    
    # Group by payment type
    by_payment = {}
    for s in sales:
        pt = s.get("payment_type", "cash")
        by_payment[pt] = by_payment.get(pt, 0) + s.get("final_total", 0)
    
    return {
        "total_sales": len(sales),
        "total_revenue": total_revenue,
        "total_profit": total_profit,
        "by_payment_type": by_payment,
        "start_date": start_date,
        "end_date": end_date
    }

@router.get("/top-products")
async def get_top_products(
    limit: int = 10,
    current_user: dict = Depends(get_current_user)
):
    """Get top selling products"""
    tenant_id = current_user.get("tenant_id")
    target_db = get_tenant_db(tenant_id) if tenant_id else db
    
    pipeline = [
        {"$unwind": "$items"},
        {"$group": {
            "_id": "$items.product_id",
            "product_name": {"$first": "$items.product_name"},
            "total_quantity": {"$sum": "$items.quantity"},
            "total_revenue": {"$sum": "$items.total"}
        }},
        {"$sort": {"total_quantity": -1}},
        {"$limit": limit}
    ]
    
    results = await target_db.sales.aggregate(pipeline).to_list(limit)
    return results
