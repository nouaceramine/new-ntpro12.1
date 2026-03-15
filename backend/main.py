"""
NT Commerce 12.0 - Legendary Build
Main application entry point with modular architecture
"""
from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, File, UploadFile, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from contextvars import ContextVar
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Literal
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
import io
import requests as http_requests
import asyncio
import shutil
import base64
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Load environment variables from .env file
load_dotenv()

# Try to import resend
try:
    import resend
    RESEND_AVAILABLE = True
except ImportError:
    RESEND_AVAILABLE = False

# Import SendGrid
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Email, To, Content, HtmlContent
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False

# Import Stripe via emergentintegrations
try:
    from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Initialize resend if available
if RESEND_AVAILABLE:
    resend.api_key = os.environ.get('RESEND_API_KEY', '')

# MongoDB connection
# NOTE: config/database.py is the canonical source for DB config.
# These definitions are kept here because 11,000+ lines reference them directly.
# Future refactoring should import from config.database instead.
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
main_db = client[os.environ['DB_NAME']]  # Main SaaS database (plans, tenants, agents, super admin users)

# ContextVar for per-request tenant database isolation
_tenant_db_ctx: ContextVar = ContextVar('tenant_db')

class _TenantDBProxy:
    """Proxy that routes DB calls to tenant-specific DB when in tenant context, otherwise main DB.
    This ensures data isolation: each tenant's requests automatically use their own database."""
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

db = _TenantDBProxy()  # All existing code uses `db` - now routes to correct tenant DB automatically

# Multi-tenancy: Get tenant-specific database
def get_tenant_db(tenant_id: str):
    """Get database for a specific tenant"""
    if not tenant_id:
        return main_db
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

# JWT Settings
SECRET_KEY = os.environ['JWT_SECRET_KEY']
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

# Currency
CURRENCY = "دج"  # Algerian Dinar

# Create the main app
app = FastAPI(title="NT API")

# Initialize rate limiter (slowapi)
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

security = HTTPBearer()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create static directory for uploads
UPLOAD_DIR = ROOT_DIR / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ============ IMPORT ROBOT & SERVICES ============
from robots.robot_manager import RobotManager
from services.notification_service import NotificationService
from services.sms_service import SMSService
from services.email_service import EmailService

# ============ IMPORT REFACTORED ROUTES ============
from routes.saas_routes import router as saas_router, get_super_admin
from routes.database_routes import router as database_router
from routes import system_errors as system_errors_routes

# ============ IMPORT NEW AI & ACCOUNTING ROUTES ============
from routes.ai.chat_routes import create_ai_routes
from routes.accounting.accounting_routes import create_accounting_routes
from routes.settings_routes import create_settings_routes
from routes.whatsapp_routes import create_whatsapp_routes
from routes.tax_routes import create_tax_routes
from routes.notification_routes import create_notification_routes
from routes.currency_routes import create_currency_routes
from routes.performance_routes import create_performance_routes, record_request_time
from routes.banking_routes import create_banking_routes
from routes.repair_routes import create_repair_routes
from routes.printing_routes import create_printing_routes, create_barcode_routes
from routes.defective_routes import create_defective_routes
from routes.backup_routes import create_backup_routes
from routes.security_routes import create_security_routes
from routes.wallet_routes import create_wallet_routes
from routes.supplier_tracking_routes import create_supplier_tracking_routes
from routes.search_routes import create_search_routes
from routes.task_chat_routes import create_task_routes, create_chat_routes
from routes.permissions_routes import create_permissions_routes
from routes.smart_notifications_routes import create_smart_notifications_routes
from routes.products_routes import create_products_routes
from routes.customers_routes import create_customers_routes
from routes.sales_routes import create_sales_routes
from routes.purchases_routes import create_purchases_routes
from routes.stats_routes import create_stats_routes
from routes.employees_routes import create_employees_routes
from routes.cashbox_routes import create_cashbox_routes
from routes.debts_routes import create_debts_routes
from routes.expenses_routes import create_expenses_routes
from routes.daily_sessions_routes import create_daily_sessions_routes
from routes.suppliers_core_routes import create_suppliers_routes
from routes.warehouse_core_routes import create_warehouse_routes
from routes.customer_debts_routes import create_customer_debts_routes
from routes.ai_assistant_routes import create_ai_assistant_routes
from routes.advanced_sales_routes import create_advanced_sales_routes
from routes.online_store_routes import create_online_store_routes
from routes.sendgrid_email_routes import create_sendgrid_email_routes
from routes.sms_marketing_routes import create_sms_marketing_routes
from routes.stripe_routes import create_stripe_routes
from routes.sendgrid_integration_routes import create_sendgrid_integration_routes
from routes.whatsapp_integration_routes import create_whatsapp_integration_routes
from routes.yalidine_integration_routes import create_yalidine_integration_routes
from routes.push_notification_routes import create_push_notification_routes
from utils.permissions import create_permission_checker

# ============ IMPORT MODELS FROM MODULES ============
from models.schemas import *
from models.accounting.schemas import *
from models.ai.schemas import *

# ============ INITIALIZE SERVICES & ROBOT MANAGER ============
notification_service = NotificationService(main_db)
sms_service = SMSService(main_db)
email_service = EmailService()
robot_manager = RobotManager(main_db, client, notification_service, sms_service, email_service)


# ============ ADDITIONAL MODELS (Not in schemas.py yet) ============

class DailySessionCreate(BaseModel):
    opening_cash: float = 0
    notes: str = ""
    cash_box_id: str = "cash"

class DailySessionClose(BaseModel):
    closing_cash: float
    notes: str = ""
    cash_breakdown: dict = {}

class DailySessionResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    session_code: str
    date: str
    opening_cash: float
    closing_cash: Optional[float] = None
    expected_cash: float = 0
    difference: float = 0
    total_sales: float = 0
    total_purchases: float = 0
    total_expenses: float = 0
    sales_count: int = 0
    purchases_count: int = 0
    is_closed: bool = False
    user_id: str
    user_name: str
    cash_box_id: str = "cash"
    notes: str = ""
    cash_breakdown: dict = {}
    created_at: str
    closed_at: Optional[str] = None

class InventorySessionCreate(BaseModel):
    name: str = ""
    code: Optional[str] = None
    warehouse_id: str = "main"
    family_filter: str = "all"
    status: str = "active"
    started_at: Optional[str] = None
    counted_items: Optional[dict] = {}
    notes: str = ""

class InventoryItemUpdate(BaseModel):
    product_id: str
    counted_quantity: int

class InventorySessionUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    counted_items: Optional[dict] = None
    completed_at: Optional[str] = None
    applied_changes: Optional[bool] = None
    notes: Optional[str] = None

class InventorySessionResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str = ""
    code: Optional[str] = None
    session_code: Optional[str] = None
    warehouse_id: str = "main"
    family_filter: str = "all"
    status: str
    items: List[dict] = []
    counted_items: dict = {}
    total_products: int = 0
    counted_products: int = 0
    discrepancies: int = 0
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    notes: str = ""
    started_at: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
    closed_at: Optional[str] = None
    applied_changes: bool = False

class DebtPaymentCreate(BaseModel):
    amount: float
    payment_method: str = "cash"
    notes: str = ""

class ApiKeyCreate(BaseModel):
    name: str
    service: str
    description: str = ""

class ApiKeyResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    service: str
    key_preview: str
    description: str = ""
    is_active: bool = True
    created_at: str

class RechargeTransactionCreate(BaseModel):
    service_type: str
    phone_number: str
    amount: float
    operator: str

class RechargeTransactionResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    service_type: str
    phone_number: str
    amount: float
    operator: str
    status: str
    profit: float = 0
    user_id: str
    user_name: str = ""
    created_at: str

class PhoneDirectoryCreate(BaseModel):
    name: str
    phone: str
    category: str = "general"
    notes: str = ""

class PhoneDirectoryResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    phone: str
    category: str
    notes: str = ""
    created_at: str

class NotificationCreate(BaseModel):
    title: str
    message: str
    type: str = "info"
    target_roles: List[str] = []

class NotificationResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    title: str
    message: str
    type: str
    is_read: bool = False
    target_roles: List[str] = []
    created_by: str
    created_at: str

class RepairCreate(BaseModel):
    customer_name: str
    customer_phone: str
    device_type: str
    device_model: str
    issue_description: str
    estimated_cost: float = 0
    notes: str = ""

class RepairUpdate(BaseModel):
    status: Optional[str] = None
    diagnosis: Optional[str] = None
    repair_notes: Optional[str] = None
    parts_used: Optional[List[dict]] = None
    final_cost: Optional[float] = None
    technician_id: Optional[str] = None

class RepairResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    repair_code: str
    customer_name: str
    customer_phone: str
    device_type: str
    device_model: str
    issue_description: str
    diagnosis: str = ""
    repair_notes: str = ""
    status: str
    estimated_cost: float
    final_cost: float = 0
    parts_used: List[dict] = []
    technician_id: Optional[str] = None
    technician_name: str = ""
    notes: str = ""
    received_at: str
    completed_at: Optional[str] = None
    delivered_at: Optional[str] = None

class SparePartCreate(BaseModel):
    name: str
    compatible_models: str = ""
    quantity: int = 0
    purchase_price: float = 0
    selling_price: float = 0
    min_stock: int = 5

class SparePartResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    compatible_models: str = ""
    quantity: int
    purchase_price: float
    selling_price: float
    min_stock: int
    created_at: str

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    session_id: Optional[str] = None

class ImageOCRRequest(BaseModel):
    image_base64: str

class OCRResponse(BaseModel):
    extracted_models: List[str]
    raw_text: str

# ============ HELPER FUNCTIONS ============

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        user_type = payload.get("type")  # admin, agent, tenant
        tenant_id = payload.get("tenant_id")
        
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # For tenant users, get from tenant database
        if user_type == "tenant" and tenant_id:
            tenant_db = get_tenant_db(tenant_id)
            user = await tenant_db.users.find_one({"id": user_id}, {"_id": 0, "password": 0, "hashed_password": 0})
            
            # Get tenant info from main_db to get plan features
            tenant = await main_db.saas_tenants.find_one({"id": tenant_id}, {"_id": 0, "password": 0})
            
            if user is None:
                # Check main tenant record (always in main_db)
                if tenant:
                    user = {
                        "id": tenant["id"],
                        "email": tenant["email"],
                        "name": tenant["name"],
                        "role": "admin",
                        "tenant_id": tenant_id,
                        "user_type": "tenant",
                        "company_name": tenant.get("company_name", ""),
                        "created_at": tenant.get("created_at", datetime.now(timezone.utc).isoformat())
                    }
                else:
                    raise HTTPException(status_code=401, detail="User not found")
            else:
                user["tenant_id"] = tenant_id
                user["user_type"] = "tenant"
                if not user.get("created_at"):
                    user["created_at"] = datetime.now(timezone.utc).isoformat()
            
            # Add plan features and limits for tenant users
            if tenant:
                plan = await main_db.saas_plans.find_one({"id": tenant.get("plan_id")}, {"_id": 0})
                if plan:
                    user["features"] = {**plan.get("features", {}), **tenant.get("features_override", {})}
                    user["limits"] = {**plan.get("limits", {}), **tenant.get("limits_override", {})}
                user["company_name"] = tenant.get("company_name", "")
        else:
            # For admin users, get from main database
            user = await main_db.users.find_one({"id": user_id}, {"_id": 0, "password": 0, "hashed_password": 0})
            if user is None:
                raise HTTPException(status_code=401, detail="User not found")
            user["user_type"] = user_type or "admin"
            if tenant_id:
                user["tenant_id"] = tenant_id
        
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_tenant_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user and their tenant database"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        user_type = payload.get("type")
        tenant_id = payload.get("tenant_id")
        
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Get the appropriate database
        if user_type == "tenant" and tenant_id:
            tenant_db = get_tenant_db(tenant_id)
        else:
            tenant_db = main_db  # Use main database for admin users
            tenant_id = None
        
        # Get user info
        user = await tenant_db.users.find_one({"id": user_id}, {"_id": 0, "password": 0, "hashed_password": 0})
        if user is None and tenant_id:
            # For tenant owner, create entry from saas_tenants
            tenant = await main_db.saas_tenants.find_one({"id": tenant_id}, {"_id": 0, "password": 0})
            if tenant:
                user = {
                    "id": tenant["id"],
                    "email": tenant["email"],
                    "name": tenant["name"],
                    "role": "admin"
                }
        
        if user is None:
            user = await main_db.users.find_one({"id": user_id}, {"_id": 0, "password": 0, "hashed_password": 0})
        
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        return {"user": user, "db": tenant_db, "tenant_id": tenant_id}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_admin_user(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    if not current_user.get("id"):
        raise HTTPException(status_code=403, detail="Invalid admin identity")
    if current_user.get("is_active") is False:
        raise HTTPException(status_code=403, detail="Account is deactivated")
    return current_user

async def get_tenant_admin(current_user: dict = Depends(get_current_user)):
    """Require tenant context - rejects super_admin users without tenant_id.
    Use this for tenant-specific data routes (products, customers, sales, etc.)."""
    if not current_user.get("tenant_id"):
        raise HTTPException(status_code=403, detail="هذا الإجراء متاح فقط لمشتركي المنصة")
    if current_user.get("role") not in ["admin", "manager", "user", "tenant_admin"]:
        raise HTTPException(status_code=403, detail="صلاحيات غير كافية")
    return current_user

async def require_tenant(current_user: dict = Depends(get_current_user)):
    """Require tenant context for read operations - any authenticated tenant user."""
    if not current_user.get("tenant_id"):
        raise HTTPException(status_code=403, detail="هذا الإجراء متاح فقط لمشتركي المنصة")
    return current_user

async def generate_invoice_number(prefix: str) -> str:
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    count = await db.counters.find_one_and_update(
        {"_id": f"{prefix}_{today}"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True
    )
    return f"{prefix}-{today}-{count['seq']:04d}"

async def init_cash_boxes():
    """Initialize default cash boxes if they don't exist, or update existing ones with name_fr"""
    boxes = [
        {"id": "cash", "name": "الصندوق النقدي", "name_fr": "Caisse", "type": "cash", "balance": 0},
        {"id": "bank", "name": "الحساب البنكي", "name_fr": "Compte bancaire", "type": "bank", "balance": 0},
        {"id": "wallet", "name": "المحفظة الإلكترونية", "name_fr": "Portefeuille électronique", "type": "wallet", "balance": 0},
        {"id": "safe", "name": "الخزنة", "name_fr": "Coffre-fort", "type": "safe", "balance": 0}
    ]
    for box in boxes:
        existing = await db.cash_boxes.find_one({"id": box["id"]})
        if not existing:
            box["updated_at"] = datetime.now(timezone.utc).isoformat()
            await db.cash_boxes.insert_one(box)
        elif not existing.get("name_fr"):
            # Update existing box with name_fr if missing
            await db.cash_boxes.update_one(
                {"id": box["id"]},
                {"$set": {"name_fr": box["name_fr"]}}
            )

async def init_default_data(tenant_db):
    """Initialize default data for a tenant (customers, suppliers, families, products)"""
    now = datetime.now(timezone.utc).isoformat()
    
    # Default Customer Family
    default_customer_family_id = "default-customer-family"
    existing_cf = await tenant_db.customer_families.find_one({"id": default_customer_family_id})
    if not existing_cf:
        await tenant_db.customer_families.insert_one({
            "id": default_customer_family_id,
            "name": "عائلة زبائن متنوعة",
            "name_fr": "Famille clients divers",
            "description": "عائلة افتراضية للزبائن",
            "discount": 0,
            "created_at": now,
            "updated_at": now
        })
    
    # Default Customer
    default_customer_id = "default-customer"
    existing_c = await tenant_db.customers.find_one({"id": default_customer_id})
    if not existing_c:
        await tenant_db.customers.insert_one({
            "id": default_customer_id,
            "name": "زبون متنوع",
            "name_fr": "Client divers",
            "phone": "",
            "email": "",
            "address": "",
            "family_id": default_customer_family_id,
            "family_name": "عائلة زبائن متنوعة",
            "balance": 0,
            "total_purchases": 0,
            "notes": "زبون افتراضي للمبيعات العامة",
            "created_at": now,
            "updated_at": now
        })
    
    # Default Supplier Family
    default_supplier_family_id = "default-supplier-family"
    existing_sf = await tenant_db.supplier_families.find_one({"id": default_supplier_family_id})
    if not existing_sf:
        await tenant_db.supplier_families.insert_one({
            "id": default_supplier_family_id,
            "name": "عائلة مورد متنوع",
            "name_fr": "Famille fournisseurs divers",
            "description": "عائلة افتراضية للموردين",
            "created_at": now,
            "updated_at": now
        })
    
    # Default Supplier
    default_supplier_id = "default-supplier"
    existing_s = await tenant_db.suppliers.find_one({"id": default_supplier_id})
    if not existing_s:
        await tenant_db.suppliers.insert_one({
            "id": default_supplier_id,
            "name": "مورد متنوع",
            "name_fr": "Fournisseur divers",
            "phone": "",
            "email": "",
            "address": "",
            "family_id": default_supplier_family_id,
            "family_name": "عائلة مورد متنوع",
            "balance": 0,
            "total_purchases": 0,
            "notes": "مورد افتراضي للمشتريات العامة",
            "created_at": now,
            "updated_at": now
        })
    
    # Default Product Family
    default_product_family_id = "default-product-family"
    existing_pf = await tenant_db.product_families.find_one({"id": default_product_family_id})
    if not existing_pf:
        await tenant_db.product_families.insert_one({
            "id": default_product_family_id,
            "name": "عائلة منتج متنوع",
            "name_fr": "Famille produits divers",
            "name_ar": "عائلة منتج متنوع",
            "name_en": "Various Products Family",
            "description": "عائلة افتراضية للمنتجات",
            "description_ar": "عائلة افتراضية للمنتجات المتنوعة",
            "description_en": "Default family for various products",
            "parent_id": "",
            "parent_name": "",
            "image": "",
            "created_at": now,
            "updated_at": now
        })
    
    # Default Product
    default_product_id = "default-product"
    existing_p = await tenant_db.products.find_one({"id": default_product_id})
    if not existing_p:
        await tenant_db.products.insert_one({
            "id": default_product_id,
            "name_ar": "منتج متنوع",
            "name_en": "Produit divers",
            "article_code": "DIVERS-001",
            "barcode": "",
            "family_id": default_product_family_id,
            "family_name": "عائلة منتج متنوع",
            "purchase_price": 0,
            "wholesale_price": 0,
            "retail_price": 0,
            "quantity": 0,
            "min_stock": 0,
            "unit": "وحدة",
            "description": "منتج افتراضي للمبيعات المتنوعة",
            "supplier_id": default_supplier_id,
            "supplier_name": "مورد متنوع",
            "image": "",
            "created_at": now,
            "updated_at": now
        })


# ============ PERMISSION SYSTEM ============
require_permission = create_permission_checker(db, get_current_user)

# ============ MODULAR ROUTES (extracted from legacy inline routes) ============
from routes.auth_users_routes import create_auth_users_routes
from routes.utility_routes import create_utility_routes
from routes.notifications_routes import create_notifications_routes
from routes.ocr_invoice_routes import create_ocr_invoice_routes
from routes.recharge_sim_routes import create_recharge_sim_routes
from routes.shipping_loyalty_routes import create_shipping_loyalty_routes
from routes.families_permissions_routes import create_families_permissions_routes
from routes.system_sync_routes import create_system_sync_routes

auth_users_router = create_auth_users_routes(
    db, main_db, get_current_user, get_admin_user, get_tenant_admin, require_tenant,
    get_tenant_db, hash_password, verify_password, create_access_token,
    init_tenant_database, init_default_data, init_cash_boxes,
    SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_HOURS, security,
    UserCreate, UserLogin, UserUpdate, UserResponse, TokenResponse, PasswordUpdate,
    limiter=limiter
)
utility_router = create_utility_routes(db, require_tenant, get_tenant_admin, PriceHistoryResponse)
notifications_router = create_notifications_routes(db, require_tenant, get_tenant_admin, get_current_user, DEFAULT_PERMISSIONS)
ocr_invoice_router = create_ocr_invoice_routes(db, require_tenant, get_tenant_admin, CURRENCY, ApiKeyCreate, ApiKeyResponse, ImageOCRRequest, OCRResponse, generate_invoice_number)
recharge_sim_router = create_recharge_sim_routes(db, require_tenant, get_tenant_admin, RECHARGE_CONFIG, RechargeCreate, RechargeResponse)
shipping_loyalty_router = create_shipping_loyalty_routes(db, require_tenant, get_tenant_admin, CURRENCY)
families_permissions_router = create_families_permissions_routes(db, require_tenant, get_tenant_admin, get_admin_user, DEFAULT_PERMISSIONS, ROLE_DESCRIPTIONS, PERMISSION_CATEGORIES, UPLOAD_DIR, ProductFamilyCreate, ProductFamilyUpdate, ProductFamilyResponse, ProductResponse)
system_sync_router = create_system_sync_routes(db, main_db, client, require_tenant, get_tenant_admin, get_current_user, get_super_admin, logger)

# Include router and middleware
# ============ LEGENDARY BUILD - NEW ROUTES (registered BEFORE api_router to avoid conflicts) ============

# Repair System (16 collections)
repair_router = create_repair_routes(db, get_current_user, get_tenant_admin)
app.include_router(repair_router, prefix="/api")

# Printing & Barcode System
printing_router = create_printing_routes(db, get_current_user, get_tenant_admin)
app.include_router(printing_router, prefix="/api")
barcode_router = create_barcode_routes(db, get_current_user, get_tenant_admin)
app.include_router(barcode_router, prefix="/api")

# Defective Goods System (11 collections)
defective_router = create_defective_routes(db, get_current_user, get_tenant_admin)
app.include_router(defective_router, prefix="/api")

# Backup System (5 collections)
backup_router = create_backup_routes(db, main_db, get_current_user, get_tenant_admin, get_super_admin)
app.include_router(backup_router, prefix="/api")

# Advanced Security (9 collections)
security_router = create_security_routes(db, main_db, get_current_user, get_super_admin)
app.include_router(security_router, prefix="/api")

# Wallet & Payments
wallet_router = create_wallet_routes(db, main_db, get_current_user, get_tenant_admin, get_super_admin)
app.include_router(wallet_router, prefix="/api")

# Supplier Tracking
supplier_tracking_router = create_supplier_tracking_routes(db, get_current_user, get_tenant_admin)
app.include_router(supplier_tracking_router, prefix="/api")

# Ultra Search
search_router = create_search_routes(db, get_current_user)
app.include_router(search_router, prefix="/api")

# Task Management & Internal Chat
task_router = create_task_routes(db, get_current_user, get_tenant_admin)
app.include_router(task_router, prefix="/api")
chat_router = create_chat_routes(db, get_current_user)
app.include_router(chat_router, prefix="/api")

# Permissions System (500+ permissions)
permissions_router = create_permissions_routes(db, main_db, get_current_user, get_tenant_admin)
app.include_router(permissions_router, prefix="/api")

# Smart Notifications
smart_notif_router = create_smart_notifications_routes(db, main_db, get_current_user)
app.include_router(smart_notif_router, prefix="/api")

# Core Business Routes (Extracted from server.py)
products_router = create_products_routes(db, get_current_user, get_tenant_admin, require_tenant)
app.include_router(products_router, prefix="/api")
customers_router = create_customers_routes(db, get_current_user, get_tenant_admin, require_tenant)
app.include_router(customers_router, prefix="/api")
advanced_sales_router = create_advanced_sales_routes(db, get_current_user, get_tenant_admin, require_tenant)
app.include_router(advanced_sales_router, prefix="/api")
sales_extracted_router = create_sales_routes(db, get_current_user, get_tenant_admin, require_tenant)
app.include_router(sales_extracted_router, prefix="/api")
purchases_extracted_router = create_purchases_routes(db, get_current_user, get_tenant_admin, require_tenant)
app.include_router(purchases_extracted_router, prefix="/api")
stats_router = create_stats_routes(db, get_current_user, get_tenant_admin, require_tenant, init_cash_boxes, CURRENCY)
app.include_router(stats_router, prefix="/api")
employees_router = create_employees_routes(db, get_current_user, get_tenant_admin, require_tenant, DEFAULT_PERMISSIONS)
app.include_router(employees_router, prefix="/api")
cashbox_router = create_cashbox_routes(db, get_current_user, get_tenant_admin, require_tenant, init_cash_boxes)
app.include_router(cashbox_router, prefix="/api")
debts_router = create_debts_routes(db, get_current_user, get_tenant_admin, require_tenant)
app.include_router(debts_router, prefix="/api")
expenses_router = create_expenses_routes(db, get_current_user, get_tenant_admin, require_tenant)
app.include_router(expenses_router, prefix="/api")
daily_sessions_router = create_daily_sessions_routes(db, get_current_user, get_tenant_admin, require_tenant)
app.include_router(daily_sessions_router, prefix="/api")
suppliers_core_router = create_suppliers_routes(db, get_current_user, get_tenant_admin, require_tenant)
app.include_router(suppliers_core_router, prefix="/api")
warehouse_core_router = create_warehouse_routes(db, get_current_user, get_tenant_admin, require_tenant)
app.include_router(warehouse_core_router, prefix="/api")
customer_debts_router = create_customer_debts_routes(db, get_current_user, get_tenant_admin, require_tenant, CURRENCY)
app.include_router(customer_debts_router, prefix="/api")
ai_assistant_router = create_ai_assistant_routes(db, get_current_user, get_tenant_admin, require_tenant)
app.include_router(ai_assistant_router, prefix="/api")

# Online Store & WooCommerce (extracted)
online_store_router = create_online_store_routes(db, main_db, get_current_user, get_tenant_admin, require_tenant, get_tenant_db)
app.include_router(online_store_router, prefix="/api")

# SendGrid Email (extracted)
sendgrid_email_router = create_sendgrid_email_routes(db, main_db, get_current_user, get_tenant_admin, require_tenant, get_super_admin)
app.include_router(sendgrid_email_router, prefix="/api")

# SMS Marketing (extracted)
sms_marketing_router = create_sms_marketing_routes(db, get_current_user, get_tenant_admin, require_tenant)
app.include_router(sms_marketing_router, prefix="/api")

# Stripe Payments (extracted)
stripe_payment_router = create_stripe_routes(db, main_db, get_current_user, get_tenant_admin, require_tenant, get_super_admin)
app.include_router(stripe_payment_router, prefix="/api")

# SendGrid Integration
sendgrid_integration_router = create_sendgrid_integration_routes(db, get_current_user, get_tenant_admin, require_tenant)
app.include_router(sendgrid_integration_router, prefix="/api")

# WhatsApp Integration
whatsapp_integration_router = create_whatsapp_integration_routes(db, get_current_user, get_tenant_admin, require_tenant)
app.include_router(whatsapp_integration_router, prefix="/api")

# Yalidine Shipping Integration
yalidine_integration_router = create_yalidine_integration_routes(db, get_current_user, get_tenant_admin, require_tenant)
app.include_router(yalidine_integration_router, prefix="/api")

# Push Notifications
push_notification_router = create_push_notification_routes(db, get_current_user, get_tenant_admin, require_tenant)
app.include_router(push_notification_router, prefix="/api")

# ============ MODULAR ROUTES (from legacy extraction) ============
app.include_router(auth_users_router, prefix="/api")
app.include_router(utility_router, prefix="/api")
app.include_router(notifications_router, prefix="/api")
app.include_router(ocr_invoice_router, prefix="/api")
app.include_router(recharge_sim_router, prefix="/api")
app.include_router(shipping_loyalty_router, prefix="/api")
app.include_router(families_permissions_router, prefix="/api")
app.include_router(system_sync_router, prefix="/api")

app.include_router(api_router)
app.include_router(saas_router, prefix="/api")  # Refactored SaaS routes
app.include_router(database_router, prefix="/api/saas")  # Database import/export routes

# Initialize and include system errors routes
system_errors_routes.init_routes(main_db, get_super_admin)
app.include_router(system_errors_routes.router, prefix="/api")  # System errors routes

# Initialize and include AI routes
ai_router = create_ai_routes(db, get_current_user)
app.include_router(ai_router, prefix="/api")  # AI chat and insights routes

# Initialize and include accounting routes
accounting_router = create_accounting_routes(db, get_current_user)
app.include_router(accounting_router, prefix="/api")  # Accounting routes

# Initialize and include settings routes
settings_router = create_settings_routes(db, get_current_user)
app.include_router(settings_router, prefix="/api")  # Settings routes

# Initialize and include WhatsApp routes
whatsapp_router = create_whatsapp_routes(db, get_current_user)
app.include_router(whatsapp_router, prefix="/api")  # WhatsApp routes

# Initialize and include Tax routes
tax_router = create_tax_routes(db, get_current_user)
app.include_router(tax_router, prefix="/api")  # Tax routes

# Initialize and include Notification routes
notification_router = create_notification_routes(db, get_current_user)
app.include_router(notification_router, prefix="/api")  # Notification routes

# Initialize and include Currency routes
currency_router = create_currency_routes(db, get_current_user)
app.include_router(currency_router, prefix="/api")  # Currency routes

# Initialize and include Performance routes
performance_router = create_performance_routes(db, get_current_user)
app.include_router(performance_router, prefix="/api")  # Performance routes

# Initialize and include Banking routes
banking_router = create_banking_routes(db, get_current_user)
app.include_router(banking_router, prefix="/api")  # Banking routes

# ============ ROBOT API ENDPOINTS ============
robot_router = APIRouter(prefix="/robots", tags=["robots"])

@robot_router.get("/status")
async def get_robot_status(admin: dict = Depends(get_super_admin)):
    return robot_manager.get_status()

@robot_router.post("/restart/{robot_name}")
async def restart_robot(robot_name: str, admin: dict = Depends(get_super_admin)):
    success = await robot_manager.restart_robot(robot_name)
    if success:
        return {"message": f"تم اعادة تشغيل روبوت {robot_name}"}
    raise HTTPException(status_code=404, detail="الروبوت غير موجود")

@robot_router.post("/run/{robot_name}")
async def run_robot_once(robot_name: str, admin: dict = Depends(get_super_admin)):
    result = await robot_manager.run_robot_once(robot_name)
    if result is not None:
        return {"message": f"تم تشغيل {robot_name} بنجاح", "stats": result}
    raise HTTPException(status_code=404, detail="الروبوت غير موجود")

@robot_router.post("/stop-all")
async def stop_all_robots(admin: dict = Depends(get_super_admin)):
    await robot_manager.stop_all()
    return {"message": "تم ايقاف جميع الروبوتات"}

@robot_router.post("/start-all")
async def start_all_robots(admin: dict = Depends(get_super_admin)):
    asyncio.create_task(robot_manager.start_all())
    return {"message": "تم بدء تشغيل جميع الروبوتات"}

app.include_router(robot_router, prefix="/api")  # Robot management routes

# Tenant context middleware - extracts tenant_id from JWT and sets ContextVar
@app.middleware("http")
async def tenant_context_middleware(request: Request, call_next):
    """Sets the tenant database context for each request based on JWT tenant_id"""
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            tenant_id = payload.get("tenant_id")
            if tenant_id:
                tenant_specific_db = client[f"tenant_{tenant_id.replace('-', '_')}"]
                _tenant_db_ctx.set(tenant_specific_db)
        except Exception:
            pass  # Invalid/expired token - no tenant context, falls back to main_db
    response = await call_next(request)
    # Record request timing for performance monitoring
    import time as _time
    return response

# Performance timing middleware
@app.middleware("http")
async def performance_timing_middleware(request: Request, call_next):
    """Track request timing for performance monitoring"""
    import time as _time
    start = _time.time()
    response = await call_next(request)
    duration = _time.time() - start
    if request.url.path.startswith("/api/"):
        record_request_time(duration, request.url.path)
    response.headers["X-Response-Time"] = f"{duration*1000:.0f}ms"
    return response

# CORS Configuration - secure origins (no wildcard fallback)
_cors_env = os.environ.get('CORS_ORIGINS', '')
_cors_origins = [o.strip() for o in _cors_env.split(',') if o.strip()] if _cors_env else []
# Always allow preview URL in development
_preview_url = os.environ.get('PREVIEW_URL', '')
if _preview_url and _preview_url not in _cors_origins:
    _cors_origins.append(_preview_url)

if not _cors_origins:
    logger.warning("CORS_ORIGINS is empty - CORS will block all cross-origin requests")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=_cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for uploads
app.mount("/api/static", StaticFiles(directory=str(ROOT_DIR / "static")), name="static")

@app.on_event("startup")
async def startup():
    await init_cash_boxes()
    # Start robots in background
    robot_manager.initialize()
    asyncio.create_task(robot_manager.start_all())
    logger.info("Robots initialized and starting in background")
    # Create indexes for better performance
    try:
        # Existing indexes
        await db.products.create_index("id", unique=True)
        await db.products.create_index("family_id")
        await db.products.create_index("barcode")
        await db.products.create_index("article_code")
        await db.customers.create_index("id", unique=True)
        await db.customers.create_index("phone")
        await db.suppliers.create_index("id", unique=True)
        await db.sales.create_index("id", unique=True)
        await db.sales.create_index("created_at")
        await db.sales.create_index("customer_id")
        await db.purchases.create_index("id", unique=True)
        await db.purchases.create_index("created_at")
        await db.purchases.create_index("items.product_id")
        await db.daily_sessions.create_index("id", unique=True)
        await db.daily_sessions.create_index("status")
        await db.transactions.create_index("created_at")
        await db.transactions.create_index("cash_box_id")
        
        # New accounting indexes
        await db.accounts.create_index("id", unique=True)
        await db.accounts.create_index("code", unique=True)
        await db.accounts.create_index("account_type")
        await db.journal_entries.create_index("id", unique=True)
        await db.journal_entries.create_index("entry_number", unique=True)
        await db.journal_entries.create_index("date")
        await db.journal_entries.create_index("status")
        await db.invoices.create_index("id", unique=True)
        await db.invoices.create_index("invoice_number", unique=True)
        await db.invoices.create_index("invoice_type")
        await db.invoices.create_index("status")
        await db.invoices.create_index("issue_date")
        await db.invoices.create_index("due_date")
        await db.invoices.create_index("customer_id")
        await db.invoices.create_index("supplier_id")
        await db.payments.create_index("id", unique=True)
        await db.payments.create_index("payment_number", unique=True)
        await db.payments.create_index("payment_type")
        await db.payments.create_index("payment_date")
        await db.expenses.create_index("id", unique=True)
        await db.expenses.create_index("expense_number", unique=True)
        await db.expenses.create_index("category")
        await db.expenses.create_index("expense_date")
        
        # AI indexes
        await db.ai_insights.create_index("id", unique=True)
        await db.ai_insights.create_index("insight_type")
        await db.ai_insights.create_index("priority")
        await db.ai_insights.create_index("is_dismissed")
        await db.chat_sessions.create_index("id", unique=True)
        await db.chat_sessions.create_index("user_id")
        await db.agent_tasks.create_index("id", unique=True)
        await db.agent_tasks.create_index("agent_type")
        await db.fraud_alerts.create_index("id", unique=True)
        await db.fraud_alerts.create_index("is_resolved")
        await db.daily_reports.create_index("id", unique=True)
        await db.daily_reports.create_index("date", unique=True)
        await db.audit_logs.create_index("id", unique=True)
        await db.audit_logs.create_index("entity_type")
        await db.audit_logs.create_index("entity_id")
        await db.audit_logs.create_index("created_at")
        
        # WhatsApp indexes
        await db.whatsapp_messages.create_index("id", unique=True)
        await db.whatsapp_messages.create_index("from_number")
        await db.whatsapp_messages.create_index("processed")
        await db.whatsapp_messages.create_index("tenant_id")
        await db.whatsapp_config.create_index("tenant_id", unique=True)
        
        # Tax indexes
        await db.tax_rates.create_index("id", unique=True)
        await db.tax_rates.create_index("type")
        await db.tax_declarations.create_index("id", unique=True)
        await db.tax_declarations.create_index("year")
        
        # Push notification indexes
        await db.push_notifications.create_index("id", unique=True)
        await db.push_notifications.create_index("tenant_id")
        await db.push_notifications.create_index("created_at")
        await db.notification_preferences.create_index("user_id", unique=True)
        
        # Currency indexes
        await db.currencies.create_index("code", unique=True)
        await db.currency_settings.create_index("tenant_id")
        await db.currency_rate_history.create_index("code")
        
        print("✅ Database indexes created successfully (including accounting & AI)")
    except Exception as e:
        print(f"⚠️ Index creation warning: {e}")

@app.on_event("shutdown")
async def shutdown_db_client():
    await robot_manager.stop_all()
    client.close()
