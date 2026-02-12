"""
Database Configuration and Connection Module
"""
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'ntcommerce')]

def get_tenant_db(tenant_id: str):
    """Get database for a specific tenant"""
    if not tenant_id:
        return db
    db_name = f"tenant_{tenant_id.replace('-', '_')}"
    return client[db_name]

async def init_tenant_database(tenant_id: str):
    """Initialize a new tenant database with default collections and data"""
    tenant_db = get_tenant_db(tenant_id)
    
    # Initialize cash boxes
    boxes = [
        {"id": "cash", "name": "الصندوق النقدي", "name_fr": "Caisse", "type": "cash", "balance": 0},
        {"id": "bank", "name": "الحساب البنكي", "name_fr": "Compte bancaire", "type": "bank", "balance": 0},
        {"id": "wallet", "name": "المحفظة الإلكترونية", "name_fr": "Portefeuille électronique", "type": "wallet", "balance": 0},
        {"id": "safe", "name": "الخزنة", "name_fr": "Coffre-fort", "type": "safe", "balance": 0}
    ]
    for box in boxes:
        existing = await tenant_db.cash_boxes.find_one({"id": box["id"]})
        if not existing:
            await tenant_db.cash_boxes.insert_one(box)
    
    # Initialize default warehouse
    existing_warehouse = await tenant_db.warehouses.find_one({"id": "main"})
    if not existing_warehouse:
        await tenant_db.warehouses.insert_one({
            "id": "main",
            "name": "المخزن الرئيسي",
            "location": "",
            "is_main": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    
    # Initialize settings
    existing_settings = await tenant_db.settings.find_one({"id": "general"})
    if not existing_settings:
        await tenant_db.settings.insert_one({
            "id": "general",
            "low_stock_threshold": 10,
            "debt_reminder_days": 30,
            "currency": "دج",
            "language": "ar"
        })
    
    logger.info(f"Initialized database for tenant: {tenant_id}")
    return tenant_db
