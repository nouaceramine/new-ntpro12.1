"""
Database configuration and connection management for NT Commerce
"""
from motor.motor_asyncio import AsyncIOMotorClient
from contextvars import ContextVar
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
main_db = client[os.environ['DB_NAME']]

# ContextVar for per-request tenant database isolation
_tenant_db_ctx: ContextVar = ContextVar('tenant_db')

class _TenantDBProxy:
    """Proxy that routes DB calls to tenant-specific DB when in tenant context, otherwise main DB."""
    def __getattr__(self, name):
        try:
            return getattr(_tenant_db_ctx.get(), name)
        except LookupError:
            return getattr(main_db, name)

    def __getitem__(self, name):
        try:
            return _tenant_db_ctx.get()[name]
        except LookupError:
            return main_db[name]

db = _TenantDBProxy()

def get_tenant_db(tenant_id: str):
    """Get database for a specific tenant"""
    if not tenant_id:
        return main_db
    db_name = f"tenant_{tenant_id.replace('-', '_')}"
    return client[db_name]

def set_tenant_context(tenant_db):
    """Set the tenant database context for current request"""
    _tenant_db_ctx.set(tenant_db)

def clear_tenant_context():
    """Clear the tenant database context"""
    try:
        _tenant_db_ctx.set(main_db)
    except:
        pass

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
    
    # Initialize system settings
    existing_settings = await tenant_db.system_settings.find_one({})
    if not existing_settings:
        await tenant_db.system_settings.insert_one({
            "company_name": "",
            "company_address": "",
            "company_phone": "",
            "company_email": "",
            "tax_rate": 0,
            "currency": "DZD",
            "language": "ar",
            "created_at": None
        })
    
    return tenant_db
