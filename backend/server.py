"""
NT Commerce API Server
Main server file with organized imports from modules
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
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'nt_commerce_super_secure_jwt_secret_key_2024_v3_hardened')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

# Currency
CURRENCY = "دج"  # Algerian Dinar

# Create the main app
app = FastAPI(title="NT API")

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
        logger.info(f"verify_password called - password length: {len(password)}, hash length: {len(hashed)}")
        logger.info(f"Hash starts with: {hashed[:10]}")
        result = bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        logger.info(f"bcrypt.checkpw result: {result}")
        return result
    except Exception as e:
        logger.error(f"verify_password error: {e}")
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

@api_router.post("/init-default-data")
async def api_init_default_data(admin: dict = Depends(get_tenant_admin)):
    """Initialize default data for existing tenant"""
    tenant_db = get_tenant_db(admin["tenant_id"])
    await init_default_data(tenant_db)
    return {"message": "تم تهيئة البيانات الافتراضية بنجاح", "status": "success"}

# ============ AUTH ROUTES ============

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user: UserCreate):
    existing = await db.users.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # SECURITY: Prevent creating super_admin or saas_admin roles
    forbidden_roles = ["super_admin", "saas_admin", "superadmin"]
    if user.role and user.role.lower() in [r.lower() for r in forbidden_roles]:
        raise HTTPException(
            status_code=403, 
            detail="لا يمكن إنشاء حساب بصلاحية سوبر أدمين - Creating super_admin accounts is not allowed"
        )
    
    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    user_doc = {
        "id": user_id, "email": user.email,
        "password": hash_password(user.password),
        "name": user.name, "role": user.role, "created_at": now
    }
    await db.users.insert_one(user_doc)
    access_token = create_access_token({"sub": user_id, "role": user.role})
    
    return TokenResponse(
        access_token=access_token,
        user=UserResponse(id=user_id, email=user.email, name=user.name, role=user.role, created_at=now)
    )

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    logger.info(f"Login attempt for: {credentials.email}")
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    logger.info(f"User found: {user is not None}")
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Support both password and hashed_password fields
    stored_password = user.get("hashed_password") or user.get("password")
    logger.info(f"Password field exists: {stored_password is not None}")
    if not stored_password or not verify_password(credentials.password, stored_password):
        logger.info("Password verification failed")
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    logger.info("Login successful")
    access_token = create_access_token({"sub": user["id"], "role": user["role"]})
    return TokenResponse(
        access_token=access_token,
        user=UserResponse(id=user["id"], email=user["email"], name=user["name"], role=user["role"], permissions=user.get("permissions", {}), created_at=user["created_at"])
    )

# Unified Login - Auto-detect user type
class UnifiedLoginResponse(BaseModel):
    access_token: str
    user_type: str  # admin, agent, tenant
    redirect_to: str
    user: dict

# ============ BRUTE FORCE PROTECTION ============
_login_attempts = {}  # {email: {"count": int, "locked_until": str}}
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_MINUTES = 15

def _check_brute_force(email: str):
    """Check if account is locked due to too many failed attempts"""
    info = _login_attempts.get(email)
    if not info:
        return
    if info.get("locked_until"):
        locked = datetime.fromisoformat(info["locked_until"])
        if datetime.now(timezone.utc) < locked:
            remaining = int((locked - datetime.now(timezone.utc)).total_seconds() / 60) + 1
            raise HTTPException(status_code=429, detail=f"الحساب مقفل. حاول بعد {remaining} دقيقة")
        else:
            _login_attempts.pop(email, None)

def _record_failed_login(email: str):
    info = _login_attempts.get(email, {"count": 0})
    info["count"] = info.get("count", 0) + 1
    if info["count"] >= MAX_LOGIN_ATTEMPTS:
        info["locked_until"] = (datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_MINUTES)).isoformat()
    _login_attempts[email] = info

def _clear_failed_login(email: str):
    _login_attempts.pop(email, None)

@api_router.post("/auth/unified-login")
async def unified_login(credentials: UserLogin):
    """
    Unified login endpoint that auto-detects user type:
    1. Check if user is an admin/employee
    2. Check if user is an agent
    3. Check if user is a tenant
    """
    email = credentials.email
    password = credentials.password
    
    # Brute force protection
    _check_brute_force(email)
    
    # 1. Check Admin/Employee users first
    user = await db.users.find_one({"email": email}, {"_id": 0})
    if user:
        stored_password = user.get("hashed_password") or user.get("password")
        if stored_password and verify_password(password, stored_password):
            _clear_failed_login(email)
            access_token = create_access_token({"sub": user["id"], "role": user["role"]})
            return {
                "access_token": access_token,
                "user_type": "admin",
                "redirect_to": "/saas-admin",
                "user": {
                    "id": user["id"],
                    "email": user["email"],
                    "name": user["name"],
                    "role": user["role"],
                    "permissions": user.get("permissions", {})
                }
            }
    
    # 2. Check Agents
    agent = await db.saas_agents.find_one({"email": email}, {"_id": 0})
    if agent:
        stored_password = agent.get("password", "")
        try:
            if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                if not agent.get("is_active", True):
                    raise HTTPException(status_code=403, detail="الحساب معطل")
                _clear_failed_login(email)
                
                token_data = {
                    "sub": agent["id"],
                    "email": agent["email"],
                    "role": "agent",
                    "type": "agent"
                }
                access_token = create_access_token(token_data)
                return {
                    "access_token": access_token,
                    "user_type": "agent",
                    "redirect_to": "/agent/dashboard",
                    "user": {
                        "id": agent["id"],
                        "email": agent["email"],
                        "name": agent["name"],
                        "company_name": agent.get("company_name", ""),
                        "current_balance": agent.get("current_balance", 0),
                        "credit_limit": agent.get("credit_limit", 0)
                    }
                }
        except Exception:
            pass
    
    # 3. Check Tenants
    tenant = await db.saas_tenants.find_one({"email": email}, {"_id": 0})
    if tenant:
        stored_password = tenant.get("password", "")
        try:
            if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                if not tenant.get("is_active", True):
                    raise HTTPException(status_code=403, detail="الحساب معطل")
                _clear_failed_login(email)
                
                # Check subscription
                if tenant.get("subscription_ends_at"):
                    end_date = datetime.fromisoformat(tenant["subscription_ends_at"].replace("Z", "+00:00"))
                    if end_date < datetime.now(timezone.utc) and not tenant.get("is_trial"):
                        raise HTTPException(status_code=403, detail="انتهت صلاحية الاشتراك")
                
                # Check if this is the first login - create database if not initialized
                tenant_id = tenant['id']
                if not tenant.get("database_initialized", False):
                    logger.info(f"First login (unified) for tenant {tenant_id} - initializing database...")
                    tenant_db = await init_tenant_database(tenant_id)
                    
                    # Create admin user in tenant's database
                    admin_user = {
                        "id": str(uuid.uuid4()),
                        "name": tenant["name"],
                        "email": tenant["email"],
                        "password": stored_password,
                        "role": "admin",
                        "permissions": {},
                        "created_at": datetime.now(timezone.utc).isoformat()
                    }
                    await tenant_db.users.insert_one(admin_user)
                    
                    # Initialize default data (customers, suppliers, families, products)
                    await init_default_data(tenant_db)
                    
                    # Mark database as initialized
                    await db.saas_tenants.update_one(
                        {"id": tenant_id},
                        {"$set": {
                            "database_initialized": True,
                            "first_login_at": datetime.now(timezone.utc).isoformat()
                        }}
                    )
                    logger.info(f"Database initialized successfully for tenant {tenant_id}")
                
                token_data = {
                    "sub": tenant["id"],
                    "email": tenant["email"],
                    "role": "tenant_admin",
                    "type": "tenant",
                    "tenant_id": tenant["id"]
                }
                access_token = create_access_token(token_data)
                
                # Get plan info with features and limits
                plan = await db.saas_plans.find_one({"id": tenant.get("plan_id")}, {"_id": 0})
                features = {**plan.get("features", {}), **tenant.get("features_override", {})} if plan else {}
                limits = {**plan.get("limits", {}), **tenant.get("limits_override", {})} if plan else {}
                
                return {
                    "access_token": access_token,
                    "user_type": "tenant",
                    "redirect_to": "/tenant/dashboard",
                    "user": {
                        "id": tenant["id"],
                        "email": tenant["email"],
                        "name": tenant["name"],
                        "company_name": tenant.get("company_name", ""),
                        "plan_name": plan.get("name_ar", "") if plan else "",
                        "subscription_ends_at": tenant.get("subscription_ends_at"),
                        "database_name": f"tenant_{tenant['id'].replace('-', '_')}",
                        "is_first_login": not tenant.get("database_initialized", False),
                        "features": features,
                        "limits": limits
                    }
                }
        except HTTPException:
            raise
        except Exception:
            pass
    
    # No user found
    _record_failed_login(email)
    raise HTTPException(status_code=401, detail="بيانات الدخول غير صحيحة")

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(**current_user)

# ============ TWO-FACTOR AUTHENTICATION (2FA) ============
import pyotp
import qrcode
import io
import base64

@api_router.post("/auth/2fa/setup")
async def setup_2fa(current_user: dict = Depends(get_current_user)):
    """Generate 2FA secret and QR code for user"""
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=current_user.get("email", ""), issuer_name="NT Commerce")
    # Generate QR code as base64
    qr = qrcode.make(uri)
    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()
    # Save secret - check both main_db and tenant db
    user_db = main_db
    user = await main_db.users.find_one({"id": current_user["id"]})
    if not user:
        user_db = db
        user = await db.users.find_one({"id": current_user["id"]})
    if not user:
        # Try looking up tenants
        user_db = main_db
        user = await main_db.tenants.find_one({"id": current_user["id"]})
    if user:
        coll = main_db.tenants if user.get("plan_name") or user.get("plan_id") else user_db.users
        await coll.update_one(
            {"id": current_user["id"]},
            {"$set": {"two_fa_secret_pending": secret}}
        )
    # Generate backup codes
    backup_codes = [pyotp.random_base32()[:8] for _ in range(6)]
    return {
        "secret": secret,
        "qr_code": f"data:image/png;base64,{qr_base64}",
        "uri": uri,
        "backup_codes": backup_codes,
    }

@api_router.post("/auth/2fa/verify")
async def verify_2fa(data: dict, current_user: dict = Depends(get_current_user)):
    """Verify and activate 2FA with a code"""
    code = data.get("code", "")
    # Look up user in multiple locations
    user = await main_db.users.find_one({"id": current_user["id"]}, {"_id": 0})
    user_coll = main_db.users
    if not user:
        user = await db.users.find_one({"id": current_user["id"]}, {"_id": 0})
        user_coll = db.users
    if not user:
        user = await main_db.tenants.find_one({"id": current_user["id"]}, {"_id": 0})
        user_coll = main_db.tenants
    if not user:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")
    secret = user.get("two_fa_secret_pending") or user.get("two_fa_secret")
    if not secret:
        raise HTTPException(status_code=400, detail="قم بإعداد 2FA أولا")
    totp = pyotp.TOTP(secret)
    if totp.verify(code):
        await user_coll.update_one(
            {"id": current_user["id"]},
            {"$set": {"two_fa_secret": secret, "two_fa_enabled": True}, "$unset": {"two_fa_secret_pending": ""}}
        )
        return {"message": "تم تفعيل المصادقة الثنائية بنجاح", "enabled": True}
    raise HTTPException(status_code=400, detail="الرمز غير صحيح")

@api_router.post("/auth/2fa/disable")
async def disable_2fa(data: dict, current_user: dict = Depends(get_current_user)):
    """Disable 2FA"""
    code = data.get("code", "")
    user = await main_db.users.find_one({"id": current_user["id"]}, {"_id": 0})
    user_coll = main_db.users
    if not user:
        user = await db.users.find_one({"id": current_user["id"]}, {"_id": 0})
        user_coll = db.users
    if not user:
        user = await main_db.tenants.find_one({"id": current_user["id"]}, {"_id": 0})
        user_coll = main_db.tenants
    if not user or not user.get("two_fa_secret"):
        raise HTTPException(status_code=400, detail="2FA غير مفعل")
    totp = pyotp.TOTP(user["two_fa_secret"])
    if totp.verify(code):
        await user_coll.update_one(
            {"id": current_user["id"]},
            {"$set": {"two_fa_enabled": False}, "$unset": {"two_fa_secret": "", "two_fa_secret_pending": ""}}
        )
        return {"message": "تم إلغاء تفعيل المصادقة الثنائية", "enabled": False}
    raise HTTPException(status_code=400, detail="الرمز غير صحيح")

@api_router.get("/auth/2fa/status")
async def get_2fa_status(current_user: dict = Depends(get_current_user)):
    """Check if 2FA is enabled for current user"""
    user = await main_db.users.find_one({"id": current_user["id"]}, {"_id": 0, "two_fa_enabled": 1})
    if not user:
        user = await db.users.find_one({"id": current_user["id"]}, {"_id": 0, "two_fa_enabled": 1})
    if not user:
        user = await main_db.tenants.find_one({"id": current_user["id"]}, {"_id": 0, "two_fa_enabled": 1})
    return {"enabled": user.get("two_fa_enabled", False) if user else False}

# ============ USER MANAGEMENT ============

@api_router.get("/users", response_model=List[UserResponse])
async def get_all_users(admin: dict = Depends(get_admin_user)):
    users = await db.users.find({}, {"_id": 0, "password": 0}).to_list(1000)
    return [UserResponse(**u) for u in users]

class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: str = "user"

@api_router.post("/users", response_model=UserResponse)
async def create_user(user_data: UserCreate, admin: dict = Depends(get_admin_user)):
    """Create a new user (admin only)"""
    # SECURITY: Prevent creating super_admin or saas_admin roles
    forbidden_roles = ["super_admin", "saas_admin", "superadmin"]
    if user_data.role and user_data.role.lower() in [r.lower() for r in forbidden_roles]:
        # Only super_admin can create super_admin users
        if admin.get("role") != "super_admin":
            raise HTTPException(
                status_code=403, 
                detail="لا يمكن إنشاء حساب بصلاحية سوبر أدمين - Creating super_admin accounts is not allowed"
            )
    
    # Check if email already exists
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="البريد الإلكتروني مستخدم بالفعل")
    
    if len(user_data.password) < 4:
        raise HTTPException(status_code=400, detail="كلمة المرور يجب أن تكون 4 أحرف على الأقل")
    
    now = datetime.now(timezone.utc).isoformat()
    new_user = {
        "id": str(uuid.uuid4()),
        "name": user_data.name,
        "email": user_data.email,
        "password": hash_password(user_data.password),
        "role": user_data.role,
        "tenant_id": admin.get("tenant_id"),
        "permissions": {},
        "created_at": now
    }
    
    await db.users.insert_one(new_user)
    
    # Return without password
    del new_user["password"]
    return UserResponse(**new_user)

@api_router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, updates: UserUpdate, admin: dict = Depends(get_admin_user)):
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # SECURITY: Prevent changing role to super_admin or saas_admin
    forbidden_roles = ["super_admin", "saas_admin", "superadmin"]
    if updates.role and updates.role.lower() in [r.lower() for r in forbidden_roles]:
        # Only super_admin can assign super_admin role
        if admin.get("role") != "super_admin":
            raise HTTPException(
                status_code=403, 
                detail="لا يمكن تعيين صلاحية سوبر أدمين - Cannot assign super_admin role"
            )
    
    # SECURITY: Prevent non-super_admin from modifying super_admin users
    if user.get("role") == "super_admin" and admin.get("role") != "super_admin":
        raise HTTPException(
            status_code=403, 
            detail="لا يمكن تعديل حساب سوبر أدمين - Cannot modify super_admin account"
        )
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    if update_data:
        await db.users.update_one({"id": user_id}, {"$set": update_data})
    updated = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
    return UserResponse(**updated)

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str, admin: dict = Depends(get_admin_user)):
    if admin["id"] == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}

@api_router.put("/users/{user_id}/password")
async def update_user_password(user_id: str, password_data: PasswordUpdate, admin: dict = Depends(get_admin_user)):
    """Update user password (admin only)"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if len(password_data.new_password) < 4:
        raise HTTPException(status_code=400, detail="كلمة المرور يجب أن تكون 4 أحرف على الأقل")
    
    hashed = hash_password(password_data.new_password)
    await db.users.update_one({"id": user_id}, {"$set": {"password": hashed}})
    
    return {"message": "تم تحديث كلمة المرور بنجاح"}

# ============ CODE GENERATORS FOR ALL ENTITIES ============


@api_router.get("/suppliers/generate-code")
async def generate_supplier_code():
    """Generate next supplier code (FR0001/26, etc.)"""
    year = str(datetime.now().year)[2:]  # 2026 -> 26
    pipeline = [
        {"$match": {"code": {"$regex": f"^FR\\d{{4}}/{year}$"}}},
        {"$project": {"num": {"$toInt": {"$substr": ["$code", 2, 4]}}}},
        {"$sort": {"num": -1}},
        {"$limit": 1}
    ]
    result = await db.suppliers.aggregate(pipeline).to_list(1)
    next_num = result[0]["num"] + 1 if result else 1
    return {"code": f"FR{str(next_num).zfill(4)}/{year}"}



@api_router.get("/expenses/generate-code")
async def generate_expense_code():
    """Generate next expense code (CH0001/26, etc.)"""
    year = str(datetime.now().year)[2:]  # 2026 -> 26
    pipeline = [
        {"$match": {"code": {"$regex": f"^CH\\d{{4}}/{year}$"}}},
        {"$project": {"num": {"$toInt": {"$substr": ["$code", 2, 4]}}}},
        {"$sort": {"num": -1}},
        {"$limit": 1}
    ]
    result = await db.expenses.aggregate(pipeline).to_list(1)
    next_num = result[0]["num"] + 1 if result else 1
    return {"code": f"CH{str(next_num).zfill(4)}/{year}"}

@api_router.get("/inventory-sessions/generate-code")
async def generate_inventory_code():
    """Generate next inventory code (IN0001/26, etc.)"""
    year = str(datetime.now().year)[2:]  # 2026 -> 26
    pipeline = [
        {"$match": {"code": {"$regex": f"^IN\\d{{4}}/{year}$"}}},
        {"$project": {"num": {"$toInt": {"$substr": ["$code", 2, 4]}}}},
        {"$sort": {"num": -1}},
        {"$limit": 1}
    ]
    result = await db.inventory_sessions.aggregate(pipeline).to_list(1)
    next_num = result[0]["num"] + 1 if result else 1
    return {"code": f"IN{str(next_num).zfill(4)}/{year}"}

@api_router.get("/price-updates/generate-code")
async def generate_price_update_code():
    """Generate next price update code (MT0001/26, etc.)"""
    year = str(datetime.now().year)[2:]  # 2026 -> 26
    pipeline = [
        {"$match": {"code": {"$regex": f"^MT\\d{{4}}/{year}$"}}},
        {"$project": {"num": {"$toInt": {"$substr": ["$code", 2, 4]}}}},
        {"$sort": {"num": -1}},
        {"$limit": 1}
    ]
    result = await db.price_update_logs.aggregate(pipeline).to_list(1)
    next_num = result[0]["num"] + 1 if result else 1
    return {"code": f"MT{str(next_num).zfill(4)}/{year}"}

@api_router.get("/daily-sessions/generate-code")
async def generate_session_code():
    """Generate next session code (S001/26, etc.)"""
    year = str(datetime.now().year)[2:]  # 2026 -> 26
    pipeline = [
        {"$match": {"code": {"$regex": f"^S\\d{{3}}/{year}$"}}},
        {"$project": {"num": {"$toInt": {"$substr": ["$code", 1, 3]}}}},
        {"$sort": {"num": -1}},
        {"$limit": 1}
    ]
    result = await db.daily_sessions.aggregate(pipeline).to_list(1)
    next_num = result[0]["num"] + 1 if result else 1
    return {"code": f"S{str(next_num).zfill(3)}/{year}"}

# ============ PRICE HISTORY ROUTES ============

@api_router.get("/products/{product_id}/price-history", response_model=List[PriceHistoryResponse])
async def get_product_price_history(product_id: str, user: dict = Depends(require_tenant)):
    """Get price change history for a specific product"""
    history = await db.price_history.find(
        {"product_id": product_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return [PriceHistoryResponse(**h) for h in history]

@api_router.get("/products/{product_id}/purchase-history")
async def get_product_purchase_history(product_id: str, user: dict = Depends(require_tenant)):
    """Get purchase history for a specific product (from suppliers)"""
    # Get purchases containing this product
    purchases = await db.purchases.find(
        {"items.product_id": product_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    result = []
    for purchase in purchases:
        supplier = await db.suppliers.find_one({"id": purchase.get("supplier_id")}, {"_id": 0, "name": 1, "phone": 1})
        
        # Find the item for this product
        item_data = None
        for item in purchase.get("items", []):
            if item.get("product_id") == product_id:
                item_data = item
                break
        
        if item_data:
            result.append({
                "id": purchase.get("id"),
                "date": purchase.get("created_at"),
                "supplier_id": purchase.get("supplier_id"),
                "supplier_name": supplier.get("name") if supplier else "",
                "supplier_phone": supplier.get("phone") if supplier else "",
                "quantity": item_data.get("quantity", 0),
                "unit_price": item_data.get("unit_price", 0),
                "total": item_data.get("total", 0),
                "purchase_total": purchase.get("total", 0),
                "payment_status": purchase.get("payment_status", ""),
                "notes": purchase.get("notes", "")
            })
    
    return result

@api_router.get("/products/{product_id}/sales-history")
async def get_product_sales_history(product_id: str, user: dict = Depends(require_tenant)):
    """Get sales history for a specific product"""
    # Get sales containing this product
    sales = await db.sales.find(
        {"items.product_id": product_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    result = []
    for sale in sales:
        customer = None
        if sale.get("customer_id"):
            customer = await db.customers.find_one({"id": sale.get("customer_id")}, {"_id": 0, "name": 1})
        
        # Find the item for this product
        item_data = None
        for item in sale.get("items", []):
            if item.get("product_id") == product_id:
                item_data = item
                break
        
        if item_data:
            result.append({
                "id": sale.get("id"),
                "date": sale.get("created_at"),
                "customer_name": customer.get("name") if customer else (language_ar := "زبون عابر"),
                "quantity": item_data.get("quantity", 0),
                "unit_price": item_data.get("unit_price", 0),
                "discount": item_data.get("discount", 0),
                "total": item_data.get("total", 0),
                "sale_total": sale.get("total", 0),
                "payment_type": sale.get("payment_type", "cash")
            })
    
    return result

@api_router.get("/price-history", response_model=List[PriceHistoryResponse])
async def get_all_price_history(
    limit: int = 50,
    price_type: Optional[str] = None,
    user: dict = Depends(require_tenant)
):
    """Get all price change history"""
    query = {}
    if price_type:
        query["price_type"] = price_type
    
    history = await db.price_history.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).to_list(limit)
    return [PriceHistoryResponse(**h) for h in history]

class BlacklistEntry(BaseModel):
    phone: str
    reason: str = ""
    notes: str = ""

class BlacklistResponse(BaseModel):
    id: str
    phone: str
    reason: str
    notes: str
    added_by: str
    added_by_name: str = ""
    created_at: str

@api_router.get("/blacklist")
async def get_blacklist(user: dict = Depends(require_tenant)):
    """Get all blacklisted phone numbers"""
    blacklist = await db.customer_blacklist.find({}, {"_id": 0}).sort("created_at", -1).to_list(500)
    return blacklist

@api_router.post("/blacklist")
async def add_to_blacklist(entry: BlacklistEntry, user: dict = Depends(require_tenant)):
    """Add phone to blacklist"""
    # Check if already blacklisted
    existing = await db.customer_blacklist.find_one({"phone": entry.phone})
    if existing:
        raise HTTPException(status_code=400, detail="هذا الرقم موجود بالفعل في القائمة السوداء")
    
    blacklist_doc = {
        "id": str(uuid.uuid4()),
        "phone": entry.phone,
        "reason": entry.reason,
        "notes": entry.notes,
        "added_by": user["id"],
        "added_by_name": user.get("name", ""),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.customer_blacklist.insert_one(blacklist_doc)
    
    # Mark any customers with this phone as blacklisted
    await db.customers.update_many(
        {"phone": entry.phone},
        {"$set": {"is_blacklisted": True, "blacklist_reason": entry.reason}}
    )
    
    return BlacklistResponse(**blacklist_doc)

@api_router.delete("/blacklist/{entry_id}")
async def remove_from_blacklist(entry_id: str, user: dict = Depends(require_tenant)):
    """Remove phone from blacklist"""
    entry = await db.customer_blacklist.find_one({"id": entry_id})
    if not entry:
        raise HTTPException(status_code=404, detail="لم يتم العثور على السجل")
    
    # Remove blacklist flag from customers with this phone
    await db.customers.update_many(
        {"phone": entry["phone"]},
        {"$set": {"is_blacklisted": False, "blacklist_reason": ""}}
    )
    
    await db.customer_blacklist.delete_one({"id": entry_id})
    return {"message": "تم إزالة الرقم من القائمة السوداء"}

@api_router.get("/blacklist/check/{phone}")
async def check_blacklist(phone: str, user: dict = Depends(require_tenant)):
    """Check if a phone is blacklisted"""
    entry = await db.customer_blacklist.find_one({"phone": phone}, {"_id": 0})
    return {"is_blacklisted": entry is not None, "entry": entry}

# ============ DEBT REMINDERS ============

class DebtReminderSettings(BaseModel):
    enabled: bool = True
    reminder_days: List[int] = [7, 14, 30]  # Days after debt to remind
    min_debt_amount: float = 1000  # Minimum debt to trigger reminder

@api_router.get("/debt-reminders/settings")
async def get_debt_reminder_settings(user: dict = Depends(require_tenant)):
    """Get debt reminder settings"""
    settings = await db.system_settings.find_one({"type": "debt_reminders"}, {"_id": 0})
    if not settings:
        return DebtReminderSettings().model_dump()
    return settings

@api_router.put("/debt-reminders/settings")
async def update_debt_reminder_settings(settings: DebtReminderSettings, user: dict = Depends(require_tenant)):
    """Update debt reminder settings"""
    await db.system_settings.update_one(
        {"type": "debt_reminders"},
        {"$set": {**settings.model_dump(), "type": "debt_reminders", "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )
    return {"success": True, "message": "تم حفظ إعدادات التذكير"}

@api_router.get("/debt-reminders/pending")
async def get_pending_debt_reminders(user: dict = Depends(require_tenant)):
    """Get customers with pending debt reminders"""
    settings = await db.system_settings.find_one({"type": "debt_reminders"})
    if not settings or not settings.get("enabled", True):
        return []
    
    reminder_days = settings.get("reminder_days", [7, 14, 30])
    min_amount = settings.get("min_debt_amount", 1000)
    
    # Get all customers with debt
    customers_with_debt = await db.customers.find(
        {"total_debt": {"$gte": min_amount}},
        {"_id": 0}
    ).to_list(500)
    
    reminders = []
    now = datetime.now(timezone.utc)
    
    for customer in customers_with_debt:
        # Get last sale date for this customer
        last_sale = await db.sales.find_one(
            {"customer_id": customer["id"], "payment_type": {"$in": ["credit", "partial"]}},
            sort=[("created_at", -1)]
        )
        
        if last_sale:
            try:
                sale_date_str = last_sale.get("created_at", now.isoformat())
                if 'T' in sale_date_str:
                    sale_date = datetime.fromisoformat(sale_date_str.replace('Z', '+00:00'))
                else:
                    sale_date = datetime.strptime(sale_date_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                sale_date = now
            
            days_since = (now - sale_date).days
            
            # Check if we should remind based on settings
            for reminder_day in reminder_days:
                if days_since >= reminder_day:
                    reminders.append({
                        "customer_id": customer["id"],
                        "customer_name": customer["name"],
                        "phone": customer.get("phone", ""),
                        "total_debt": customer["total_debt"],
                        "days_since_last_purchase": days_since,
                        "reminder_level": reminder_day,
                        "is_urgent": days_since >= 30
                    })
                    break  # Only one reminder per customer
    
    # Sort by urgency and debt amount
    reminders.sort(key=lambda x: (-x["days_since_last_purchase"], -x["total_debt"]))
    return reminders

@api_router.post("/debt-reminders/dismiss/{customer_id}")
async def dismiss_debt_reminder(customer_id: str, days: int = 7, user: dict = Depends(require_tenant)):
    """Dismiss a debt reminder for a period"""
    await db.debt_reminder_dismissals.update_one(
        {"customer_id": customer_id},
        {"$set": {
            "customer_id": customer_id,
            "dismissed_until": (datetime.now(timezone.utc) + timedelta(days=days)).isoformat(),
            "dismissed_by": user["id"]
        }},
        upsert=True
    )
    return {"message": f"تم تأجيل التذكير لمدة {days} أيام"}

# ============ NOTIFICATIONS ============

@api_router.get("/notifications")
async def get_notifications(user: dict = Depends(require_tenant)):
    """Get all notifications for current user"""
    notifications = await db.notifications.find(
        {"$or": [{"user_id": user["id"]}, {"user_id": None}]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    return notifications

@api_router.post("/notifications")
async def create_notification(
    title: str,
    message: str,
    notification_type: str = "info",
    user_id: Optional[str] = None,
    user: dict = Depends(require_tenant)
):
    """Create a notification"""
    notification_doc = {
        "id": str(uuid.uuid4()),
        "title": title,
        "message": message,
        "type": notification_type,  # info, warning, error, debt
        "user_id": user_id,  # None = all users
        "is_read": False,
        "created_by": user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.notifications.insert_one(notification_doc)
    return notification_doc

@api_router.put("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, user: dict = Depends(require_tenant)):
    """Mark notification as read"""
    await db.notifications.update_one(
        {"id": notification_id},
        {"$set": {"is_read": True, "read_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": "تم تحديد الإشعار كمقروء"}

@api_router.delete("/notifications/{notification_id}")
async def delete_notification(notification_id: str, user: dict = Depends(require_tenant)):
    """Delete a notification"""
    await db.notifications.delete_one({"id": notification_id})
    return {"message": "تم حذف الإشعار"}

@api_router.get("/notifications/unread-count")
async def get_unread_notification_count(user: dict = Depends(require_tenant)):
    """Get count of unread notifications"""
    count = await db.notifications.count_documents({
        "$or": [{"user_id": user["id"]}, {"user_id": None}],
        "is_read": False
    })
    return {"count": count}

# ============ NOTIFICATIONS ============

@api_router.get("/notifications")
async def get_notifications(user: dict = Depends(require_tenant)):
    # Get notifications for this user or global notifications (without user_id)
    notifications = await db.notifications.find(
        {
            "read": False,
            "$or": [
                {"user_id": user["id"]},
                {"user_id": {"$exists": False}}
            ]
        }, {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    return notifications

@api_router.put("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, user: dict = Depends(require_tenant)):
    await db.notifications.update_one(
        {"id": notification_id, "$or": [{"user_id": user["id"]}, {"user_id": {"$exists": False}}]},
        {"$set": {"read": True}}
    )
    return {"message": "Notification marked as read"}

@api_router.put("/notifications/read-all")
async def mark_all_notifications_read(user: dict = Depends(require_tenant)):
    await db.notifications.update_many(
        {"read": False, "$or": [{"user_id": user["id"]}, {"user_id": {"$exists": False}}]},
        {"$set": {"read": True}}
    )
    return {"message": "All notifications marked as read"}

@api_router.post("/notifications/generate")
async def generate_auto_notifications(user: dict = Depends(require_tenant)):
    """Generate automatic notifications for low stock and due debts"""
    notifications_created = []
    
    # 1. Low stock notifications
    low_stock_products = await db.products.find({
        "$expr": {"$lt": ["$quantity", {"$ifNull": ["$low_stock_threshold", 10]}]}
    }).to_list(100)
    
    for product in low_stock_products:
        # Check if notification already exists for this product
        existing = await db.notifications.find_one({
            "type": "low_stock",
            "reference_id": product["id"],
            "read": False
        })
        if not existing:
            notif = {
                "id": str(uuid.uuid4()),
                "type": "low_stock",
                "reference_id": product["id"],
                "message_ar": f"تنبيه: المنتج '{product.get('name_ar', product.get('name_en', 'منتج'))}' مخزونه منخفض ({product['quantity']} قطعة)",
                "message_en": f"Alert: Product '{product.get('name_en', product.get('name_ar', 'Product'))}' is low on stock ({product['quantity']} units)",
                "read": False,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.notifications.insert_one(notif)
            notifications_created.append(notif["id"])
    
    # 2. Customer debt notifications (debts > 7 days)
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    overdue_sales = await db.sales.find({
        "remaining": {"$gt": 0},
        "created_at": {"$lt": week_ago}
    }).to_list(100)
    
    for sale in overdue_sales:
        existing = await db.notifications.find_one({
            "type": "overdue_debt",
            "reference_id": sale["id"],
            "read": False
        })
        if not existing:
            customer = await db.customers.find_one({"id": sale.get("customer_id")})
            customer_name = customer["name"] if customer else "عميل"
            notif = {
                "id": str(uuid.uuid4()),
                "type": "overdue_debt",
                "reference_id": sale["id"],
                "message_ar": f"تذكير: دين مستحق من {customer_name} بقيمة {sale['remaining']:.2f} دج",
                "message_en": f"Reminder: Overdue debt from {customer_name} of {sale['remaining']:.2f} DA",
                "read": False,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.notifications.insert_one(notif)
            notifications_created.append(notif["id"])
    
    # 3. Supplier debt notifications (debts > 7 days)
    overdue_purchases = await db.purchases.find({
        "remaining": {"$gt": 0},
        "created_at": {"$lt": week_ago}
    }).to_list(100)
    
    for purchase in overdue_purchases:
        existing = await db.notifications.find_one({
            "type": "supplier_debt",
            "reference_id": purchase["id"],
            "read": False
        })
        if not existing:
            notif = {
                "id": str(uuid.uuid4()),
                "type": "supplier_debt",
                "reference_id": purchase["id"],
                "message_ar": f"تذكير: دين للمورد {purchase.get('supplier_name', '')} بقيمة {purchase['remaining']:.2f} دج",
                "message_en": f"Reminder: Supplier debt to {purchase.get('supplier_name', '')} of {purchase['remaining']:.2f} DA",
                "read": False,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.notifications.insert_one(notif)
            notifications_created.append(notif["id"])
    
    return {
        "message": f"Generated {len(notifications_created)} notifications",
        "notification_ids": notifications_created
    }

# ============ EXCEL IMPORT/EXPORT ============

@api_router.get("/products/export/excel")
async def export_products_excel(admin: dict = Depends(get_tenant_admin)):
    import pandas as pd
    
    products = await db.products.find({}, {"_id": 0}).to_list(10000)
    
    # Prepare data
    data = []
    for p in products:
        data.append({
            "الباركود": p.get("barcode", ""),
            "الاسم (عربي)": p.get("name_ar", ""),
            "الاسم (إنجليزي)": p.get("name_en", ""),
            "الوصف (عربي)": p.get("description_ar", ""),
            "الوصف (إنجليزي)": p.get("description_en", ""),
            "سعر الشراء": p.get("purchase_price", 0),
            "سعر الجملة": p.get("wholesale_price", 0),
            "سعر التجزئة": p.get("retail_price", 0),
            "الكمية": p.get("quantity", 0),
            "حد المخزون المنخفض": p.get("low_stock_threshold", 10),
            "الموديلات المتوافقة": ", ".join(p.get("compatible_models", [])),
            "رابط الصورة": p.get("image_url", "")
        })
    
    df = pd.DataFrame(data)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='المنتجات')
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=products.xlsx"}
    )

from fastapi import UploadFile, File

@api_router.post("/products/import/excel")
async def import_products_excel(file: UploadFile = File(...), admin: dict = Depends(get_tenant_admin)):
    import pandas as pd
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="File must be Excel format (.xlsx or .xls)")
    
    contents = await file.read()
    df = pd.read_excel(io.BytesIO(contents))
    
    now = datetime.now(timezone.utc).isoformat()
    imported = 0
    updated = 0
    errors = []
    
    for index, row in df.iterrows():
        try:
            barcode = str(row.get("الباركود", "")).strip()
            name_ar = str(row.get("الاسم (عربي)", "")).strip()
            name_en = str(row.get("الاسم (إنجليزي)", "")).strip()
            
            if not name_ar and not name_en:
                continue
            
            product_data = {
                "barcode": barcode,
                "name_ar": name_ar or name_en,
                "name_en": name_en or name_ar,
                "description_ar": str(row.get("الوصف (عربي)", "")),
                "description_en": str(row.get("الوصف (إنجليزي)", "")),
                "purchase_price": float(row.get("سعر الشراء", 0) or 0),
                "wholesale_price": float(row.get("سعر الجملة", 0) or 0),
                "retail_price": float(row.get("سعر التجزئة", 0) or 0),
                "quantity": int(row.get("الكمية", 0) or 0),
                "low_stock_threshold": int(row.get("حد المخزون المنخفض", 10) or 10),
                "compatible_models": [m.strip() for m in str(row.get("الموديلات المتوافقة", "")).split(",") if m.strip()],
                "image_url": str(row.get("رابط الصورة", "")),
                "updated_at": now
            }
            
            # Check if product exists by barcode or name
            existing = None
            if barcode:
                existing = await db.products.find_one({"barcode": barcode})
            if not existing and name_ar:
                existing = await db.products.find_one({"name_ar": name_ar})
            
            if existing:
                await db.products.update_one({"id": existing["id"]}, {"$set": product_data})
                updated += 1
            else:
                product_data["id"] = str(uuid.uuid4())
                product_data["created_at"] = now
                await db.products.insert_one(product_data)
                imported += 1
                
        except Exception as e:
            errors.append(f"Row {index + 2}: {str(e)}")
    
    return {
        "imported": imported,
        "updated": updated,
        "errors": errors[:10]  # Return first 10 errors
    }

# ============ SELECTIVE DATA DELETE ============

class SelectiveDeleteRequest(BaseModel):
    data_types: List[str]  # ["sales", "purchases", "customers", etc.]
    confirm_code: str

@api_router.post("/system/selective-delete")
async def selective_delete(request: SelectiveDeleteRequest, admin: dict = Depends(get_tenant_admin)):
    """Selectively delete specific data types"""
    if request.confirm_code != "DELETE-SELECTED":
        raise HTTPException(status_code=400, detail="Invalid confirmation code")
    
    # Check permissions
    user_permissions = admin.get("permissions") or DEFAULT_PERMISSIONS.get(admin.get("role", "user"), {})
    if not user_permissions.get("factory_reset", False):
        raise HTTPException(status_code=403, detail="No permission for data deletion")
    
    # Valid data types
    valid_types = {
        "sales": "sales",
        "purchases": "purchases",
        "customers": "customers",
        "suppliers": "suppliers",
        "products": "products",
        "employees": "employees",
        "debts": "debts",
        "expenses": "expenses",
        "repairs": "repairs",
        "inventory_adjustments": "inventory_adjustments",
        "daily_sessions": "daily_sessions",
        "notifications": "notifications"
    }
    
    deleted_counts = {}
    for data_type in request.data_types:
        if data_type in valid_types:
            collection_name = valid_types[data_type]
            result = await db[collection_name].delete_many({})
            deleted_counts[data_type] = result.deleted_count
            
            # Also delete related data
            if data_type == "sales":
                await db.debt_payments.delete_many({"type": "sale"})
            elif data_type == "customers":
                await db.customer_families.delete_many({})
            elif data_type == "suppliers":
                await db.supplier_families.delete_many({})
            elif data_type == "products":
                await db.product_families.delete_many({})
    
    # Log deletion
    await db.system_logs.insert_one({
        "id": str(uuid.uuid4()),
        "action": "selective_delete",
        "performed_by": admin.get("name", ""),
        "deleted_types": request.data_types,
        "deleted_counts": deleted_counts,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"success": True, "deleted_counts": deleted_counts}

# ============ SIDEBAR ORDER SETTINGS ============

@api_router.get("/settings/sidebar-order")
async def get_sidebar_order(user: dict = Depends(require_tenant)):
    """Get sidebar menu order for user"""
    settings = await db.user_settings.find_one({"user_id": user["id"]}, {"_id": 0})
    if settings and "sidebar_order" in settings:
        return {"sidebar_order": settings["sidebar_order"]}
    return {"sidebar_order": None}  # Return null to use default order

class SidebarMenuItem(BaseModel):
    id: str
    path: Optional[str] = None
    icon: Optional[str] = None
    labelAr: Optional[str] = None
    labelFr: Optional[str] = None
    visible: bool = True

class SidebarSection(BaseModel):
    id: str
    titleAr: Optional[str] = None
    titleFr: Optional[str] = None
    icon: Optional[str] = None
    visible: bool = True
    isCustom: bool = False
    items: List[SidebarMenuItem] = []

@api_router.put("/settings/sidebar-order")
async def update_sidebar_order(order: List[SidebarSection], user: dict = Depends(require_tenant)):
    """Update sidebar menu order for user"""
    # Convert to dict for storage
    order_data = [section.model_dump() for section in order]
    await db.user_settings.update_one(
        {"user_id": user["id"]},
        {"$set": {"sidebar_order": order_data, "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )
    return {"success": True}

# ============ NOTIFICATION MANAGEMENT ============

@api_router.get("/notifications/settings")
async def get_notification_settings(user: dict = Depends(require_tenant)):
    """Get notification settings"""
    settings = await db.notification_settings.find_one({"user_id": user["id"]}, {"_id": 0})
    if not settings:
        # Default settings
        settings = {
            "low_stock_enabled": True,
            "low_stock_threshold": 10,
            "debt_reminder_enabled": True,
            "debt_reminder_days": 7,
            "cash_difference_enabled": True,
            "cash_difference_threshold": 1000,
            "expense_reminder_enabled": True,
            "repair_status_enabled": True,
            "email_notifications": False,
            "sound_enabled": True
        }
    return settings

@api_router.put("/notifications/settings")
async def update_notification_settings(settings: dict, user: dict = Depends(require_tenant)):
    """Update notification settings"""
    settings["user_id"] = user["id"]
    settings["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.notification_settings.update_one(
        {"user_id": user["id"]},
        {"$set": settings},
        upsert=True
    )
    return {"success": True}

@api_router.get("/notifications/all")
async def get_all_notifications(
    skip: int = 0, 
    limit: int = 50,
    unread_only: bool = False,
    user: dict = Depends(require_tenant)
):
    """Get all notifications with pagination"""
    query = {}
    if unread_only:
        query["read"] = False
    
    notifications = await db.notifications.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    total = await db.notifications.count_documents(query)
    unread_count = await db.notifications.count_documents({"read": False})
    
    return {
        "notifications": notifications,
        "total": total,
        "unread_count": unread_count
    }

@api_router.put("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, user: dict = Depends(require_tenant)):
    """Mark a notification as read"""
    await db.notifications.update_one(
        {"id": notification_id},
        {"$set": {"read": True, "read_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"success": True}

@api_router.put("/notifications/mark-all-read")
async def mark_all_notifications_read(user: dict = Depends(require_tenant)):
    """Mark all notifications as read"""
    await db.notifications.update_many(
        {"read": False},
        {"$set": {"read": True, "read_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"success": True}

@api_router.delete("/notifications/{notification_id}")
async def delete_notification(notification_id: str, user: dict = Depends(require_tenant)):
    """Delete a notification"""
    await db.notifications.delete_one({"id": notification_id})
    return {"success": True}

@api_router.delete("/notifications/clear-all")
async def clear_all_notifications(admin: dict = Depends(get_tenant_admin)):
    """Clear all notifications"""
    result = await db.notifications.delete_many({})
    return {"success": True, "deleted_count": result.deleted_count}

# ============ OCR ROUTE ============

@api_router.post("/ocr/extract-models", response_model=OCRResponse)
async def extract_models_from_image(request: OCRRequest, admin: dict = Depends(get_tenant_admin)):
    from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent
    
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="OCR service not configured")
    
    try:
        chat = LlmChat(
            api_key=api_key,
            session_id=f"ocr-{uuid.uuid4()}",
            system_message="""You are an OCR assistant specialized in extracting phone model names from images.
            Extract all phone model names you can see in the image.
            Return ONLY the model names, one per line, without any additional text or explanation.
            Examples of model names: iPhone 15 Pro, Samsung Galaxy S24, Huawei P60 Pro, etc."""
        ).with_model("gemini", "gemini-2.5-flash")
        
        image_content = ImageContent(image_base64=request.image_base64)
        user_message = UserMessage(
            text="Extract all phone model names from this image. Return only the model names, one per line.",
            file_contents=[image_content]
        )
        
        response = await chat.send_message(user_message)
        raw_text = response.strip()
        models = [m.strip() for m in raw_text.split('\n') if m.strip()]
        
        return OCRResponse(extracted_models=models, raw_text=raw_text)
        
    except Exception as e:
        logger.error(f"OCR error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")

# ============ INVOICE PDF ============

@api_router.get("/sales/{sale_id}/invoice-pdf")
async def get_invoice_pdf(sale_id: str, user: dict = Depends(require_tenant)):
    sale = await db.sales.find_one({"id": sale_id}, {"_id": 0})
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    
    # Get sale code if exists
    sale_code = sale.get("code", "")
    
    # Generate simple HTML invoice
    items_html = ""
    for i, item in enumerate(sale["items"], 1):
        barcode = item.get('barcode', '-')
        items_html += f"""
        <tr>
            <td>{i}</td>
            <td>{barcode}</td>
            <td>{item['product_name']}</td>
            <td>{item['quantity']}</td>
            <td>{item['unit_price']:.2f} {CURRENCY}</td>
            <td>{item['discount']:.2f} {CURRENCY}</td>
            <td>{item['total']:.2f} {CURRENCY}</td>
        </tr>
        """
    
    html_content = f"""
    <!DOCTYPE html>
    <html dir="rtl" lang="ar">
    <head>
        <meta charset="UTF-8">
        <title>فاتورة {sale['invoice_number']}</title>
        <style>
            body {{ font-family: 'Cairo', Arial, sans-serif; margin: 20px; direction: rtl; }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .header h1 {{ color: #2563EB; margin: 0; }}
            .sale-code {{ font-family: monospace; font-size: 14px; background: #f0f0f0; padding: 4px 8px; border-radius: 4px; }}
            .info {{ display: flex; justify-content: space-between; margin-bottom: 20px; }}
            .info div {{ width: 48%; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 10px; text-align: right; }}
            th {{ background: #2563EB; color: white; }}
            .barcode {{ font-family: monospace; font-size: 11px; }}
            .totals {{ text-align: left; margin-top: 20px; }}
            .totals table {{ width: 300px; margin-right: 0; margin-left: auto; }}
            .footer {{ text-align: center; margin-top: 40px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>NT</h1>
            <p>فاتورة مبيعات</p>
            {f'<p class="sale-code">{sale_code}</p>' if sale_code else ''}
        </div>
        
        <div class="info">
            <div>
                <p><strong>رقم الفاتورة:</strong> {sale['invoice_number']}</p>
                <p><strong>التاريخ:</strong> {sale['created_at'][:10]}</p>
                <p><strong>البائع:</strong> {sale['created_by']}</p>
            </div>
            <div>
                <p><strong>العميل:</strong> {sale['customer_name']}</p>
                <p><strong>طريقة الدفع:</strong> {sale['payment_method']}</p>
                <p><strong>الحالة:</strong> {sale['status']}</p>
            </div>
        </div>
        
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>الباركود</th>
                    <th>المنتج</th>
                    <th>الكمية</th>
                    <th>السعر</th>
                    <th>الخصم</th>
                    <th>الإجمالي</th>
                </tr>
            </thead>
            <tbody>
                {items_html}
            </tbody>
        </table>
        
        <div class="totals">
            <table>
                <tr><td>المجموع الفرعي:</td><td>{sale['subtotal']:.2f} {CURRENCY}</td></tr>
                <tr><td>الخصم:</td><td>{sale['discount']:.2f} {CURRENCY}</td></tr>
                <tr><td><strong>الإجمالي:</strong></td><td><strong>{sale['total']:.2f} {CURRENCY}</strong></td></tr>
                <tr><td>المدفوع:</td><td>{sale['paid_amount']:.2f} {CURRENCY}</td></tr>
                <tr><td>المتبقي:</td><td>{sale['remaining']:.2f} {CURRENCY}</td></tr>
            </table>
        </div>
        
        <div class="footer">
            <p>شكراً لتعاملكم معنا</p>
        </div>
    </body>
    </html>
    """
    
    return StreamingResponse(
        io.BytesIO(html_content.encode('utf-8')),
        media_type="text/html",
        headers={"Content-Disposition": f"inline; filename=invoice_{sale['invoice_number']}.html"}
    )

# ============ API KEYS MANAGEMENT ============

import secrets

@api_router.post("/api-keys", response_model=ApiKeyResponse)
async def create_api_key(api_key: ApiKeyCreate, admin: dict = Depends(get_tenant_admin)):
    key_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    # Generate internal API key if type is internal
    generated_key = ""
    if api_key.type == "internal":
        generated_key = f"sk_{secrets.token_hex(32)}"
    
    key_value = api_key.key_value or generated_key
    
    api_key_doc = {
        "id": key_id,
        "name": api_key.name,
        "type": api_key.type,
        "service": api_key.service or "",
        "key_value": key_value,
        "secret_value": api_key.secret_value or "",
        "endpoint_url": api_key.endpoint_url or "",
        "permissions": api_key.permissions,
        "is_active": True,
        "last_used": "",
        "created_at": now
    }
    await db.api_keys.insert_one(api_key_doc)
    
    return ApiKeyResponse(
        **api_key_doc,
        key_preview=f"...{key_value[-4:]}" if len(key_value) > 4 else key_value
    )

@api_router.get("/api-keys", response_model=List[ApiKeyResponse])
async def get_api_keys(admin: dict = Depends(get_tenant_admin)):
    keys = await db.api_keys.find({}, {"_id": 0}).to_list(100)
    result = []
    for k in keys:
        k["key_preview"] = f"...{k['key_value'][-4:]}" if len(k.get('key_value', '')) > 4 else k.get('key_value', '')
        # Hide full key value
        if k["type"] == "internal":
            k["key_value"] = k["key_preview"]
        result.append(ApiKeyResponse(**k))
    return result

@api_router.get("/api-keys/{key_id}")
async def get_api_key(key_id: str, admin: dict = Depends(get_tenant_admin)):
    key = await db.api_keys.find_one({"id": key_id}, {"_id": 0})
    if not key:
        raise HTTPException(status_code=404, detail="API Key not found")
    return key

@api_router.put("/api-keys/{key_id}/toggle")
async def toggle_api_key(key_id: str, admin: dict = Depends(get_tenant_admin)):
    key = await db.api_keys.find_one({"id": key_id})
    if not key:
        raise HTTPException(status_code=404, detail="API Key not found")
    
    new_status = not key.get("is_active", True)
    await db.api_keys.update_one({"id": key_id}, {"$set": {"is_active": new_status}})
    return {"is_active": new_status}

@api_router.delete("/api-keys/{key_id}")
async def delete_api_key(key_id: str, admin: dict = Depends(get_tenant_admin)):
    result = await db.api_keys.delete_one({"id": key_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="API Key not found")
    return {"message": "API Key deleted successfully"}

# ============ RECHARGE / USSD ============

@api_router.get("/recharge/config")
async def get_recharge_config(user: dict = Depends(require_tenant)):
    """Get recharge operators configuration"""
    return RECHARGE_CONFIG

@api_router.post("/recharge", response_model=RechargeResponse)
async def create_recharge(recharge: RechargeCreate, user: dict = Depends(require_tenant)):
    """Record a recharge transaction"""
    recharge_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    # Get operator config
    operator_config = RECHARGE_CONFIG.get(recharge.operator)
    if not operator_config:
        raise HTTPException(status_code=400, detail="Invalid operator")
    
    # Calculate cost and profit
    commission_rate = operator_config.get("commission", 0) / 100
    profit = recharge.amount * commission_rate
    cost = recharge.amount - profit
    
    # Get customer name
    customer_name = "عميل نقدي"
    if recharge.customer_id:
        customer = await db.customers.find_one({"id": recharge.customer_id}, {"_id": 0, "name": 1})
        if customer:
            customer_name = customer["name"]
    
    # Generate USSD code
    ussd_template = operator_config["ussd"].get(recharge.recharge_type, "")
    ussd_code = ussd_template.replace("{phone}", recharge.phone_number).replace("{amount}", str(int(recharge.amount)))
    
    recharge_doc = {
        "id": recharge_id,
        "operator": recharge.operator,
        "operator_name": operator_config["name"],
        "phone_number": recharge.phone_number,
        "amount": recharge.amount,
        "recharge_type": recharge.recharge_type,
        "cost": cost,
        "profit": profit,
        "customer_id": recharge.customer_id or "",
        "customer_name": customer_name,
        "payment_method": recharge.payment_method,
        "status": "completed",
        "ussd_code": ussd_code,
        "notes": recharge.notes or "",
        "created_at": now,
        "created_by": user["name"]
    }
    await db.recharges.insert_one(recharge_doc)
    
    # Update cash box
    await db.cash_boxes.update_one(
        {"id": recharge.payment_method},
        {"$inc": {"balance": recharge.amount}, "$set": {"updated_at": now}}
    )
    
    # Record transaction
    await db.transactions.insert_one({
        "id": str(uuid.uuid4()),
        "cash_box_id": recharge.payment_method,
        "type": "income",
        "amount": recharge.amount,
        "description": f"شحن {operator_config['name']} - {recharge.phone_number}",
        "reference_type": "recharge",
        "reference_id": recharge_id,
        "created_at": now,
        "created_by": user["name"]
    })
    
    return RechargeResponse(**recharge_doc)

@api_router.get("/recharge", response_model=List[RechargeResponse])
async def get_recharges(
    operator: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user: dict = Depends(require_tenant)
):
    """Get recharge history"""
    query = {}
    if operator:
        query["operator"] = operator
    if start_date:
        query["created_at"] = {"$gte": start_date}
    if end_date:
        if "created_at" in query:
            query["created_at"]["$lte"] = end_date
        else:
            query["created_at"] = {"$lte": end_date}
    
    recharges = await db.recharges.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return [RechargeResponse(**r) for r in recharges]

@api_router.get("/recharge/stats")
async def get_recharge_stats(days: int = 30, admin: dict = Depends(get_tenant_admin)):
    """Get recharge statistics"""
    start_date = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    
    # Total by operator
    pipeline = [
        {"$match": {"created_at": {"$gte": start_date}}},
        {"$group": {
            "_id": "$operator",
            "count": {"$sum": 1},
            "total_amount": {"$sum": "$amount"},
            "total_profit": {"$sum": "$profit"}
        }}
    ]
    by_operator = await db.recharges.aggregate(pipeline).to_list(10)
    
    # Today's stats
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    today_stats = await db.recharges.aggregate([
        {"$match": {"created_at": {"$gte": today}}},
        {"$group": {
            "_id": None,
            "count": {"$sum": 1},
            "total_amount": {"$sum": "$amount"},
            "total_profit": {"$sum": "$profit"}
        }}
    ]).to_list(1)
    
    return {
        "by_operator": by_operator,
        "today": today_stats[0] if today_stats else {"count": 0, "total_amount": 0, "total_profit": 0},
        "period_days": days
    }

# ============ ALGERIA WILAYAS (for delivery) ============

ALGERIA_WILAYAS = {
    "01": {"name_ar": "أدرار", "name_en": "Adrar", "desk_fee": 600, "home_fee": 800},
    "02": {"name_ar": "الشلف", "name_en": "Chlef", "desk_fee": 400, "home_fee": 600},
    "03": {"name_ar": "الأغواط", "name_en": "Laghouat", "desk_fee": 500, "home_fee": 700},
    "04": {"name_ar": "أم البواقي", "name_en": "Oum El Bouaghi", "desk_fee": 450, "home_fee": 650},
    "05": {"name_ar": "باتنة", "name_en": "Batna", "desk_fee": 400, "home_fee": 600},
    "06": {"name_ar": "بجاية", "name_en": "Béjaïa", "desk_fee": 400, "home_fee": 600},
    "07": {"name_ar": "بسكرة", "name_en": "Biskra", "desk_fee": 450, "home_fee": 650},
    "08": {"name_ar": "بشار", "name_en": "Béchar", "desk_fee": 600, "home_fee": 800},
    "09": {"name_ar": "البليدة", "name_en": "Blida", "desk_fee": 300, "home_fee": 450},
    "10": {"name_ar": "البويرة", "name_en": "Bouira", "desk_fee": 350, "home_fee": 500},
    "11": {"name_ar": "تمنراست", "name_en": "Tamanrasset", "desk_fee": 800, "home_fee": 1000},
    "12": {"name_ar": "تبسة", "name_en": "Tébessa", "desk_fee": 500, "home_fee": 700},
    "13": {"name_ar": "تلمسان", "name_en": "Tlemcen", "desk_fee": 500, "home_fee": 700},
    "14": {"name_ar": "تيارت", "name_en": "Tiaret", "desk_fee": 450, "home_fee": 650},
    "15": {"name_ar": "تيزي وزو", "name_en": "Tizi Ouzou", "desk_fee": 350, "home_fee": 500},
    "16": {"name_ar": "الجزائر", "name_en": "Algiers", "desk_fee": 250, "home_fee": 400},
    "17": {"name_ar": "الجلفة", "name_en": "Djelfa", "desk_fee": 450, "home_fee": 650},
    "18": {"name_ar": "جيجل", "name_en": "Jijel", "desk_fee": 400, "home_fee": 600},
    "19": {"name_ar": "سطيف", "name_en": "Sétif", "desk_fee": 350, "home_fee": 500},
    "20": {"name_ar": "سعيدة", "name_en": "Saïda", "desk_fee": 500, "home_fee": 700},
    "21": {"name_ar": "سكيكدة", "name_en": "Skikda", "desk_fee": 400, "home_fee": 600},
    "22": {"name_ar": "سيدي بلعباس", "name_en": "Sidi Bel Abbès", "desk_fee": 500, "home_fee": 700},
    "23": {"name_ar": "عنابة", "name_en": "Annaba", "desk_fee": 400, "home_fee": 600},
    "24": {"name_ar": "قالمة", "name_en": "Guelma", "desk_fee": 450, "home_fee": 650},
    "25": {"name_ar": "قسنطينة", "name_en": "Constantine", "desk_fee": 350, "home_fee": 500},
    "26": {"name_ar": "المدية", "name_en": "Médéa", "desk_fee": 350, "home_fee": 500},
    "27": {"name_ar": "مستغانم", "name_en": "Mostaganem", "desk_fee": 450, "home_fee": 650},
    "28": {"name_ar": "المسيلة", "name_en": "M'sila", "desk_fee": 400, "home_fee": 600},
    "29": {"name_ar": "معسكر", "name_en": "Mascara", "desk_fee": 450, "home_fee": 650},
    "30": {"name_ar": "ورقلة", "name_en": "Ouargla", "desk_fee": 600, "home_fee": 800},
    "31": {"name_ar": "وهران", "name_en": "Oran", "desk_fee": 400, "home_fee": 600},
    "32": {"name_ar": "البيض", "name_en": "El Bayadh", "desk_fee": 600, "home_fee": 800},
    "33": {"name_ar": "إليزي", "name_en": "Illizi", "desk_fee": 900, "home_fee": 1100},
    "34": {"name_ar": "برج بوعريريج", "name_en": "Bordj Bou Arréridj", "desk_fee": 350, "home_fee": 500},
    "35": {"name_ar": "بومرداس", "name_en": "Boumerdès", "desk_fee": 300, "home_fee": 450},
    "36": {"name_ar": "الطارف", "name_en": "El Tarf", "desk_fee": 450, "home_fee": 650},
    "37": {"name_ar": "تندوف", "name_en": "Tindouf", "desk_fee": 900, "home_fee": 1100},
    "38": {"name_ar": "تيسمسيلت", "name_en": "Tissemsilt", "desk_fee": 450, "home_fee": 650},
    "39": {"name_ar": "الوادي", "name_en": "El Oued", "desk_fee": 550, "home_fee": 750},
    "40": {"name_ar": "خنشلة", "name_en": "Khenchela", "desk_fee": 500, "home_fee": 700},
    "41": {"name_ar": "سوق أهراس", "name_en": "Souk Ahras", "desk_fee": 500, "home_fee": 700},
    "42": {"name_ar": "تيبازة", "name_en": "Tipaza", "desk_fee": 300, "home_fee": 450},
    "43": {"name_ar": "ميلة", "name_en": "Mila", "desk_fee": 400, "home_fee": 600},
    "44": {"name_ar": "عين الدفلى", "name_en": "Aïn Defla", "desk_fee": 350, "home_fee": 500},
    "45": {"name_ar": "النعامة", "name_en": "Naâma", "desk_fee": 600, "home_fee": 800},
    "46": {"name_ar": "عين تموشنت", "name_en": "Aïn Témouchent", "desk_fee": 500, "home_fee": 700},
    "47": {"name_ar": "غرداية", "name_en": "Ghardaïa", "desk_fee": 550, "home_fee": 750},
    "48": {"name_ar": "غليزان", "name_en": "Relizane", "desk_fee": 450, "home_fee": 650},
    "49": {"name_ar": "تيميمون", "name_en": "Timimoun", "desk_fee": 800, "home_fee": 1000},
    "50": {"name_ar": "برج باجي مختار", "name_en": "Bordj Badji Mokhtar", "desk_fee": 900, "home_fee": 1100},
    "51": {"name_ar": "أولاد جلال", "name_en": "Ouled Djellal", "desk_fee": 500, "home_fee": 700},
    "52": {"name_ar": "بني عباس", "name_en": "Béni Abbès", "desk_fee": 700, "home_fee": 900},
    "53": {"name_ar": "عين صالح", "name_en": "In Salah", "desk_fee": 800, "home_fee": 1000},
    "54": {"name_ar": "عين قزام", "name_en": "In Guezzam", "desk_fee": 900, "home_fee": 1100},
    "55": {"name_ar": "توقرت", "name_en": "Touggourt", "desk_fee": 550, "home_fee": 750},
    "56": {"name_ar": "جانت", "name_en": "Djanet", "desk_fee": 900, "home_fee": 1100},
    "57": {"name_ar": "المغير", "name_en": "El M'Ghair", "desk_fee": 550, "home_fee": 750},
    "58": {"name_ar": "المنيعة", "name_en": "El Meniaa", "desk_fee": 650, "home_fee": 850}
}

@api_router.get("/delivery/wilayas")
async def get_wilayas():
    """Get all Algerian wilayas with delivery fees"""
    result = []
    for code, data in ALGERIA_WILAYAS.items():
        result.append({
            "code": code,
            "name_ar": data["name_ar"],
            "name_en": data["name_en"],
            "desk_fee": data["desk_fee"],
            "home_fee": data["home_fee"]
        })
    return sorted(result, key=lambda x: x["code"])

@api_router.get("/delivery/fee")
async def get_delivery_fee(wilaya_code: str, delivery_type: str = "desk"):
    """Calculate delivery fee for a wilaya"""
    if wilaya_code not in ALGERIA_WILAYAS:
        raise HTTPException(status_code=404, detail="Wilaya not found")
    
    wilaya = ALGERIA_WILAYAS[wilaya_code]
    fee = wilaya["home_fee"] if delivery_type == "home" else wilaya["desk_fee"]
    
    return {
        "wilaya_code": wilaya_code,
        "wilaya_name_ar": wilaya["name_ar"],
        "wilaya_name_en": wilaya["name_en"],
        "delivery_type": delivery_type,
        "fee": fee
    }

# ============ SYSTEM SETTINGS ============

class SystemSettingsUpdate(BaseModel):
    cash_difference_threshold: float = 1000  # حد التنبيه للعجز/الفائض
    low_stock_threshold: int = 10  # حد المخزون المنخفض
    currency_symbol: str = "دج"
    business_name: str = "NT"

DEFAULT_SYSTEM_SETTINGS = {
    "id": "global",
    "cash_difference_threshold": 1000,
    "low_stock_threshold": 10,
    "currency_symbol": "دج",
    "business_name": "NT"
}

@api_router.get("/system/settings")
async def get_system_settings(user: dict = Depends(require_tenant)):
    """Get system settings"""
    settings = await db.system_settings.find_one({"id": "global"}, {"_id": 0})
    if not settings:
        settings = {**DEFAULT_SYSTEM_SETTINGS}
        await db.system_settings.insert_one(settings)
    else:
        settings = {k: v for k, v in settings.items() if k != "_id"}
    return settings

@api_router.put("/system/settings")
async def update_system_settings(settings: SystemSettingsUpdate, admin: dict = Depends(get_tenant_admin)):
    """Update system settings (admin only)"""
    update_data = settings.model_dump()
    
    existing = await db.system_settings.find_one({"id": "global"})
    if existing:
        await db.system_settings.update_one(
            {"id": "global"},
            {"$set": update_data}
        )
    else:
        await db.system_settings.insert_one({**update_data, "id": "global"})
    
    return {"message": "تم تحديث الإعدادات بنجاح"}

# ============ SIM BALANCE MANAGEMENT ============

class SimSlotBalance(BaseModel):
    slot_id: int  # 1 أو 2
    operator: str  # موبيليس، جازي، أوريدو
    phone: str
    balance: float = 0
    last_updated: str = ""

class SimBalanceUpdate(BaseModel):
    balance: float
    notes: Optional[str] = ""

@api_router.get("/sim/slots")
async def get_sim_slots(admin: dict = Depends(get_tenant_admin)):
    """Get all SIM slots with their balances"""
    slots = await db.sim_slots.find({}, {"_id": 0}).to_list(10)
    if not slots:
        # Create default slots
        default_slots = [
            {"slot_id": 1, "operator": "موبيليس", "phone": "", "balance": 0, "last_updated": "", "prefix": "06"},
            {"slot_id": 2, "operator": "جازي", "phone": "", "balance": 0, "last_updated": "", "prefix": "07"},
            {"slot_id": 3, "operator": "أوريدو", "phone": "", "balance": 0, "last_updated": "", "prefix": "05"}
        ]
        await db.sim_slots.insert_many(default_slots)
        slots = default_slots
    return slots

@api_router.put("/sim/slots/{slot_id}")
async def update_sim_slot(slot_id: int, slot_data: dict, admin: dict = Depends(get_tenant_admin)):
    """Update SIM slot info"""
    now = datetime.now(timezone.utc).isoformat()
    update_data = {**slot_data, "last_updated": now}
    
    await db.sim_slots.update_one(
        {"slot_id": slot_id},
        {"$set": update_data},
        upsert=True
    )
    return {"message": "تم تحديث الشريحة بنجاح"}

@api_router.put("/sim/slots/{slot_id}/balance")
async def update_sim_balance(slot_id: int, balance_data: SimBalanceUpdate, admin: dict = Depends(get_tenant_admin)):
    """Update SIM slot balance"""
    now = datetime.now(timezone.utc).isoformat()
    
    # Get current slot
    slot = await db.sim_slots.find_one({"slot_id": slot_id})
    old_balance = slot.get("balance", 0) if slot else 0
    
    await db.sim_slots.update_one(
        {"slot_id": slot_id},
        {"$set": {"balance": balance_data.balance, "last_updated": now}}
    )
    
    # Log the balance change
    log_entry = {
        "id": str(uuid.uuid4()),
        "slot_id": slot_id,
        "old_balance": old_balance,
        "new_balance": balance_data.balance,
        "change": balance_data.balance - old_balance,
        "notes": balance_data.notes or "",
        "created_at": now,
        "created_by": admin.get("name", "")
    }
    await db.sim_balance_logs.insert_one(log_entry)
    
    return {"message": "تم تحديث الرصيد بنجاح"}

@api_router.get("/sim/slots/{slot_id}/logs")
async def get_sim_balance_logs(slot_id: int, admin: dict = Depends(get_tenant_admin)):
    """Get balance change history for a SIM slot"""
    logs = await db.sim_balance_logs.find({"slot_id": slot_id}, {"_id": 0}).sort("created_at", -1).to_list(50)
    return logs

# ============ AUTO RECHARGE BY OPERATOR ============

@api_router.post("/recharge/auto")
async def auto_recharge(phone: str, amount: float, user: dict = Depends(require_tenant)):
    """Auto-select SIM slot based on phone number prefix"""
    
    # Clean phone number
    clean_phone = phone.replace(" ", "").replace("-", "")
    if clean_phone.startswith("+213"):
        clean_phone = "0" + clean_phone[4:]
    elif clean_phone.startswith("213"):
        clean_phone = "0" + clean_phone[3:]
    
    # Determine operator by prefix
    prefix = clean_phone[:2] if len(clean_phone) >= 2 else ""
    
    operator_map = {
        "06": {"name": "موبيليس", "name_fr": "Mobilis"},
        "07": {"name": "جازي", "name_fr": "Djezzy"},
        "05": {"name": "أوريدو", "name_fr": "Ooredoo"}
    }
    
    if prefix not in operator_map:
        raise HTTPException(status_code=400, detail="رقم هاتف غير صالح. يجب أن يبدأ بـ 05, 06, أو 07")
    
    operator = operator_map[prefix]
    
    # Find the appropriate SIM slot
    slot = await db.sim_slots.find_one({"prefix": prefix}, {"_id": 0})
    
    if not slot or not slot.get("phone"):
        raise HTTPException(status_code=400, detail=f"شريحة {operator['name']} غير مفعلة")
    
    if slot.get("balance", 0) < amount:
        raise HTTPException(status_code=400, detail=f"رصيد شريحة {operator['name']} غير كافي")
    
    # Log the recharge (MOCKED)
    now = datetime.now(timezone.utc).isoformat()
    recharge_log = {
        "id": str(uuid.uuid4()),
        "phone": clean_phone,
        "amount": amount,
        "operator": operator["name"],
        "slot_id": slot["slot_id"],
        "status": "success",  # MOCKED
        "created_at": now,
        "created_by": user.get("name", "")
    }
    await db.recharge_logs.insert_one(recharge_log)
    
    # Deduct from SIM balance
    await db.sim_slots.update_one(
        {"slot_id": slot["slot_id"]},
        {"$inc": {"balance": -amount}, "$set": {"last_updated": now}}
    )
    
    return {
        "success": True,
        "phone": clean_phone,
        "amount": amount,
        "operator": operator["name"],
        "message": f"تم شحن {amount} دج لـ {clean_phone} عبر {operator['name']}"
    }

# ============ WOOCOMMERCE INTEGRATION (UI Ready) ============

class WooCommerceSettings(BaseModel):
    enabled: bool = False
    store_url: str = ""
    consumer_key: str = ""
    consumer_secret: str = ""
    sync_products: bool = True
    sync_orders: bool = True
    sync_customers: bool = True
    last_sync: str = ""

@api_router.get("/woocommerce/settings")
async def get_woocommerce_settings(admin: dict = Depends(get_tenant_admin)):
    """Get WooCommerce integration settings"""
    settings = await db.woocommerce_settings.find_one({"id": "global"}, {"_id": 0})
    if not settings:
        settings = {
            "id": "global",
            "enabled": False,
            "store_url": "",
            "consumer_key": "",
            "consumer_secret": "",
            "sync_products": True,
            "sync_orders": True,
            "sync_customers": True,
            "last_sync": ""
        }
        await db.woocommerce_settings.insert_one(settings)
    return settings

@api_router.put("/woocommerce/settings")
async def update_woocommerce_settings(settings: WooCommerceSettings, admin: dict = Depends(get_tenant_admin)):
    """Update WooCommerce integration settings"""
    update_data = settings.model_dump()
    
    await db.woocommerce_settings.update_one(
        {"id": "global"},
        {"$set": update_data},
        upsert=True
    )
    return {"message": "تم حفظ إعدادات WooCommerce"}

@api_router.post("/woocommerce/test-connection")
async def test_woocommerce_connection(admin: dict = Depends(get_tenant_admin)):
    """Test WooCommerce connection (MOCKED)"""
    settings = await db.woocommerce_settings.find_one({"id": "global"}, {"_id": 0})
    
    if not settings or not settings.get("store_url"):
        raise HTTPException(status_code=400, detail="يرجى إدخال رابط المتجر أولاً")
    
    # MOCKED - In production, actually test the API connection
    return {
        "success": True,
        "message": "تم الاتصال بالمتجر بنجاح (وضع المحاكاة)",
        "store_info": {
            "name": "متجرك",
            "url": settings.get("store_url"),
            "version": "8.0.0"
        }
    }

@api_router.post("/woocommerce/publish-product/{product_id}")
async def publish_product_to_woocommerce(product_id: str, admin: dict = Depends(get_tenant_admin)):
    """Publish a single product to WooCommerce (MOCKED)"""
    
    # Check WooCommerce settings
    wc_settings = await db.woocommerce_settings.find_one({"id": "global"}, {"_id": 0})
    if not wc_settings or not wc_settings.get("enabled"):
        raise HTTPException(status_code=400, detail="WooCommerce غير مفعل")
    
    # Get product
    product = await db.products.find_one({"id": product_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="المنتج غير موجود")
    
    now = datetime.now(timezone.utc).isoformat()
    
    # MOCKED - In production, actually call WooCommerce API
    wc_product_id = f"wc_{product_id[:8]}"
    
    # Update product with WooCommerce info
    await db.products.update_one(
        {"id": product_id},
        {"$set": {
            "woocommerce_id": wc_product_id,
            "woocommerce_status": "published",
            "woocommerce_url": f"{wc_settings.get('store_url')}/product/{product.get('name_en', '').lower().replace(' ', '-')}",
            "woocommerce_synced_at": now
        }}
    )
    
    return {
        "success": True,
        "message": f"تم نشر المنتج '{product.get('name_en')}' على المتجر",
        "woocommerce_id": wc_product_id,
        "product_url": f"{wc_settings.get('store_url')}/product/{product.get('name_en', '').lower().replace(' ', '-')}"
    }

@api_router.post("/woocommerce/publish-products")
async def publish_multiple_products_to_woocommerce(product_ids: List[str], admin: dict = Depends(get_tenant_admin)):
    """Publish multiple products to WooCommerce (MOCKED)"""
    
    # Check WooCommerce settings
    wc_settings = await db.woocommerce_settings.find_one({"id": "global"}, {"_id": 0})
    if not wc_settings or not wc_settings.get("enabled"):
        raise HTTPException(status_code=400, detail="WooCommerce غير مفعل")
    
    now = datetime.now(timezone.utc).isoformat()
    published = []
    failed = []
    
    for product_id in product_ids:
        product = await db.products.find_one({"id": product_id}, {"_id": 0})
        if not product:
            failed.append({"id": product_id, "error": "المنتج غير موجود"})
            continue
        
        # MOCKED
        wc_product_id = f"wc_{product_id[:8]}"
        
        await db.products.update_one(
            {"id": product_id},
            {"$set": {
                "woocommerce_id": wc_product_id,
                "woocommerce_status": "published",
                "woocommerce_url": f"{wc_settings.get('store_url')}/product/{product.get('name_en', '').lower().replace(' ', '-')}",
                "woocommerce_synced_at": now
            }}
        )
        
        published.append({
            "id": product_id,
            "name": product.get("name_en"),
            "woocommerce_id": wc_product_id
        })
    
    return {
        "success": True,
        "message": f"تم نشر {len(published)} منتج على المتجر",
        "published": published,
        "failed": failed
    }

@api_router.delete("/woocommerce/unpublish-product/{product_id}")
async def unpublish_product_from_woocommerce(product_id: str, admin: dict = Depends(get_tenant_admin)):
    """Remove a product from WooCommerce (MOCKED)"""
    
    product = await db.products.find_one({"id": product_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="المنتج غير موجود")
    
    # Remove WooCommerce info
    await db.products.update_one(
        {"id": product_id},
        {"$unset": {
            "woocommerce_id": "",
            "woocommerce_status": "",
            "woocommerce_url": "",
            "woocommerce_synced_at": ""
        }}
    )
    
    return {
        "success": True,
        "message": f"تم إلغاء نشر المنتج '{product.get('name_en')}' من المتجر"
    }

@api_router.post("/woocommerce/sync-inventory")
async def sync_inventory_to_woocommerce(admin: dict = Depends(get_tenant_admin)):
    """Sync all published products inventory to WooCommerce (MOCKED)"""
    
    # Get all products with woocommerce_id
    products = await db.products.find(
        {"woocommerce_id": {"$exists": True, "$ne": ""}},
        {"_id": 0}
    ).to_list(1000)
    
    now = datetime.now(timezone.utc).isoformat()
    synced_count = 0
    
    for product in products:
        # MOCKED - In production, update WooCommerce stock
        await db.products.update_one(
            {"id": product["id"]},
            {"$set": {"woocommerce_synced_at": now}}
        )
        synced_count += 1
    
    # Update last sync time
    await db.woocommerce_settings.update_one(
        {"id": "global"},
        {"$set": {"last_sync": now}}
    )
    
    return {
        "success": True,
        "message": f"تم مزامنة {synced_count} منتج",
        "synced_at": now
    }

# ============ SHIPPING/DELIVERY MANAGEMENT ============

ALGERIAN_SHIPPING_COMPANIES = [
    {"id": "yalidine", "name": "Yalidine", "name_ar": "ياليدين", "website": "https://yalidine.com", "has_api": True},
    {"id": "zr_express", "name": "ZR Express", "name_ar": "زد آر إكسبريس", "website": "https://zrexpress.com", "has_api": True},
    {"id": "maystro", "name": "Maystro Delivery", "name_ar": "مايسترو", "website": "https://maystro-delivery.com", "has_api": True},
    {"id": "ecotrack", "name": "EcoTrack", "name_ar": "إيكو تراك", "website": "https://ecotrack.dz", "has_api": True},
    {"id": "guepex", "name": "Guepex", "name_ar": "قيبكس", "website": "https://guepex.com", "has_api": True},
    {"id": "procolis", "name": "Procolis", "name_ar": "بروكوليس", "website": "https://procolis.com", "has_api": False},
    {"id": "other", "name": "Autre", "name_ar": "أخرى", "website": "", "has_api": False}
]

class ShippingCompanySettings(BaseModel):
    company_id: str
    enabled: bool = False
    api_key: str = ""
    api_secret: str = ""
    default_wilaya: str = ""
    default_commune: str = ""

class ShippingRateRequest(BaseModel):
    from_wilaya: str
    to_wilaya: str
    weight: float = 0.5  # kg
    company_id: str = ""

@api_router.get("/shipping/companies")
async def get_shipping_companies(user: dict = Depends(require_tenant)):
    """Get list of Algerian shipping companies"""
    return ALGERIAN_SHIPPING_COMPANIES

@api_router.get("/shipping/settings")
async def get_shipping_settings(admin: dict = Depends(get_tenant_admin)):
    """Get shipping integration settings"""
    settings = await db.shipping_settings.find({}, {"_id": 0}).to_list(20)
    
    # Add default settings for companies not configured
    configured_ids = {s["company_id"] for s in settings}
    for company in ALGERIAN_SHIPPING_COMPANIES:
        if company["id"] not in configured_ids:
            settings.append({
                "company_id": company["id"],
                "enabled": False,
                "api_key": "",
                "api_secret": "",
                "default_wilaya": "",
                "default_commune": ""
            })
    
    return settings

@api_router.put("/shipping/settings/{company_id}")
async def update_shipping_settings(company_id: str, settings: ShippingCompanySettings, admin: dict = Depends(get_tenant_admin)):
    """Update shipping company settings"""
    await db.shipping_settings.update_one(
        {"company_id": company_id},
        {"$set": settings.model_dump()},
        upsert=True
    )
    return {"message": "تم حفظ إعدادات شركة الشحن"}

@api_router.post("/shipping/calculate-rate")
async def calculate_shipping_rate(request: ShippingRateRequest, user: dict = Depends(require_tenant)):
    """Calculate shipping rate (MOCKED - returns estimated prices)"""
    
    # MOCKED shipping rates by wilaya distance
    base_rates = {
        "yalidine": 400,
        "zr_express": 350,
        "maystro": 380,
        "ecotrack": 420,
        "guepex": 390,
        "procolis": 450,
        "other": 500
    }
    
    # Same wilaya = lower rate
    is_same_wilaya = request.from_wilaya == request.to_wilaya
    
    rates = []
    for company in ALGERIAN_SHIPPING_COMPANIES:
        base = base_rates.get(company["id"], 400)
        if is_same_wilaya:
            price = base * 0.6
        else:
            price = base + (request.weight * 50)
        
        rates.append({
            "company_id": company["id"],
            "company_name": company["name"],
            "company_name_ar": company["name_ar"],
            "price": round(price, 2),
            "estimated_days": 2 if is_same_wilaya else 4,
            "currency": "دج"
        })
    
    return {"rates": sorted(rates, key=lambda x: x["price"])}

@api_router.get("/shipping/wilayas")
async def get_wilayas(user: dict = Depends(require_tenant)):
    """Get list of Algerian wilayas"""
    wilayas = [
        {"code": "01", "name": "أدرار", "name_fr": "Adrar"},
        {"code": "02", "name": "الشلف", "name_fr": "Chlef"},
        {"code": "03", "name": "الأغواط", "name_fr": "Laghouat"},
        {"code": "04", "name": "أم البواقي", "name_fr": "Oum El Bouaghi"},
        {"code": "05", "name": "باتنة", "name_fr": "Batna"},
        {"code": "06", "name": "بجاية", "name_fr": "Béjaïa"},
        {"code": "07", "name": "بسكرة", "name_fr": "Biskra"},
        {"code": "08", "name": "بشار", "name_fr": "Béchar"},
        {"code": "09", "name": "البليدة", "name_fr": "Blida"},
        {"code": "10", "name": "البويرة", "name_fr": "Bouira"},
        {"code": "11", "name": "تمنراست", "name_fr": "Tamanrasset"},
        {"code": "12", "name": "تبسة", "name_fr": "Tébessa"},
        {"code": "13", "name": "تلمسان", "name_fr": "Tlemcen"},
        {"code": "14", "name": "تيارت", "name_fr": "Tiaret"},
        {"code": "15", "name": "تيزي وزو", "name_fr": "Tizi Ouzou"},
        {"code": "16", "name": "الجزائر", "name_fr": "Alger"},
        {"code": "17", "name": "الجلفة", "name_fr": "Djelfa"},
        {"code": "18", "name": "جيجل", "name_fr": "Jijel"},
        {"code": "19", "name": "سطيف", "name_fr": "Sétif"},
        {"code": "20", "name": "سعيدة", "name_fr": "Saïda"},
        {"code": "21", "name": "سكيكدة", "name_fr": "Skikda"},
        {"code": "22", "name": "سيدي بلعباس", "name_fr": "Sidi Bel Abbès"},
        {"code": "23", "name": "عنابة", "name_fr": "Annaba"},
        {"code": "24", "name": "قالمة", "name_fr": "Guelma"},
        {"code": "25", "name": "قسنطينة", "name_fr": "Constantine"},
        {"code": "26", "name": "المدية", "name_fr": "Médéa"},
        {"code": "27", "name": "مستغانم", "name_fr": "Mostaganem"},
        {"code": "28", "name": "المسيلة", "name_fr": "M'Sila"},
        {"code": "29", "name": "معسكر", "name_fr": "Mascara"},
        {"code": "30", "name": "ورقلة", "name_fr": "Ouargla"},
        {"code": "31", "name": "وهران", "name_fr": "Oran"},
        {"code": "32", "name": "البيض", "name_fr": "El Bayadh"},
        {"code": "33", "name": "إليزي", "name_fr": "Illizi"},
        {"code": "34", "name": "برج بوعريريج", "name_fr": "Bordj Bou Arreridj"},
        {"code": "35", "name": "بومرداس", "name_fr": "Boumerdès"},
        {"code": "36", "name": "الطارف", "name_fr": "El Tarf"},
        {"code": "37", "name": "تندوف", "name_fr": "Tindouf"},
        {"code": "38", "name": "تيسمسيلت", "name_fr": "Tissemsilt"},
        {"code": "39", "name": "الوادي", "name_fr": "El Oued"},
        {"code": "40", "name": "خنشلة", "name_fr": "Khenchela"},
        {"code": "41", "name": "سوق أهراس", "name_fr": "Souk Ahras"},
        {"code": "42", "name": "تيبازة", "name_fr": "Tipaza"},
        {"code": "43", "name": "ميلة", "name_fr": "Mila"},
        {"code": "44", "name": "عين الدفلى", "name_fr": "Aïn Defla"},
        {"code": "45", "name": "النعامة", "name_fr": "Naâma"},
        {"code": "46", "name": "عين تموشنت", "name_fr": "Aïn Témouchent"},
        {"code": "47", "name": "غرداية", "name_fr": "Ghardaïa"},
        {"code": "48", "name": "غليزان", "name_fr": "Relizane"},
        {"code": "49", "name": "تميمون", "name_fr": "Timimoun"},
        {"code": "50", "name": "برج باجي مختار", "name_fr": "Bordj Badji Mokhtar"},
        {"code": "51", "name": "أولاد جلال", "name_fr": "Ouled Djellal"},
        {"code": "52", "name": "بني عباس", "name_fr": "Béni Abbès"},
        {"code": "53", "name": "عين صالح", "name_fr": "In Salah"},
        {"code": "54", "name": "عين قزام", "name_fr": "In Guezzam"},
        {"code": "55", "name": "توقرت", "name_fr": "Touggourt"},
        {"code": "56", "name": "جانت", "name_fr": "Djanet"},
        {"code": "57", "name": "المغير", "name_fr": "El M'Ghair"},
        {"code": "58", "name": "المنيعة", "name_fr": "El Meniaa"}
    ]
    return wilayas

# ============ LOGIN PAGE CUSTOMIZATION ============

class LoginPageSettings(BaseModel):
    logo_url: str = ""
    business_name: str = "NT"
    background_image_url: str = ""
    tagline_ar: str = "إدارة مخزون زجاج الحماية بسهولة"
    tagline_fr: str = "Gestion facile de stock de protection"

@api_router.get("/branding/settings")
async def get_branding_settings():
    """Get login page branding settings (public)"""
    settings = await db.branding_settings.find_one({"id": "global"}, {"_id": 0})
    if not settings:
        settings = {
            "id": "global",
            "logo_url": "",
            "business_name": "NT",
            "background_image_url": "",
            "tagline_ar": "إدارة مخزون زجاج الحماية بسهولة",
            "tagline_fr": "Gestion facile de stock de protection"
        }
    return settings

@api_router.put("/branding/settings")
async def update_branding_settings(settings: LoginPageSettings, admin: dict = Depends(get_tenant_admin)):
    """Update login page branding settings"""
    update_data = settings.model_dump()
    
    await db.branding_settings.update_one(
        {"id": "global"},
        {"$set": update_data},
        upsert=True
    )
    return {"message": "تم تحديث إعدادات العلامة التجارية"}

# ============ LOYALTY PROGRAM ============

class LoyaltySettings(BaseModel):
    enabled: bool = False
    points_per_dinar: float = 0.01  # نقطة لكل دينار
    points_value: float = 0.1  # قيمة النقطة بالدينار
    min_redeem_points: int = 100
    welcome_bonus: int = 0  # نقاط ترحيبية للعميل الجديد

class LoyaltyTransaction(BaseModel):
    customer_id: str
    points: int
    type: str  # earn, redeem
    sale_id: Optional[str] = None
    notes: Optional[str] = ""

@api_router.get("/loyalty/settings")
async def get_loyalty_settings(admin: dict = Depends(get_tenant_admin)):
    """Get loyalty program settings"""
    settings = await db.loyalty_settings.find_one({"id": "global"}, {"_id": 0})
    if not settings:
        settings = {
            "id": "global",
            "enabled": False,
            "points_per_dinar": 0.01,
            "points_value": 0.1,
            "min_redeem_points": 100,
            "welcome_bonus": 0
        }
        await db.loyalty_settings.insert_one(settings.copy())
    return settings

@api_router.put("/loyalty/settings")
async def update_loyalty_settings(settings: LoyaltySettings, admin: dict = Depends(get_tenant_admin)):
    """Update loyalty program settings"""
    await db.loyalty_settings.update_one(
        {"id": "global"},
        {"$set": settings.model_dump()},
        upsert=True
    )
    return {"message": "تم تحديث إعدادات برنامج الولاء"}

@api_router.get("/loyalty/customer/{customer_id}")
async def get_customer_loyalty(customer_id: str, user: dict = Depends(require_tenant)):
    """Get customer loyalty points and history"""
    customer = await db.customers.find_one({"id": customer_id}, {"_id": 0})
    if not customer:
        raise HTTPException(status_code=404, detail="العميل غير موجود")
    
    points = customer.get("loyalty_points", 0)
    
    # Get transaction history
    transactions = await db.loyalty_transactions.find(
        {"customer_id": customer_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    
    # Get loyalty settings for point value
    settings = await db.loyalty_settings.find_one({"id": "global"}, {"_id": 0})
    points_value = settings.get("points_value", 0.1) if settings else 0.1
    
    return {
        "customer_id": customer_id,
        "customer_name": customer.get("name"),
        "points": points,
        "points_value_dinar": round(points * points_value, 2),
        "transactions": transactions
    }

@api_router.post("/loyalty/earn")
async def earn_loyalty_points(transaction: LoyaltyTransaction, user: dict = Depends(require_tenant)):
    """Add loyalty points from a sale"""
    customer = await db.customers.find_one({"id": transaction.customer_id})
    if not customer:
        raise HTTPException(status_code=404, detail="العميل غير موجود")
    
    now = datetime.now(timezone.utc).isoformat()
    current_points = customer.get("loyalty_points", 0)
    new_points = current_points + transaction.points
    
    # Update customer points
    await db.customers.update_one(
        {"id": transaction.customer_id},
        {"$set": {"loyalty_points": new_points}}
    )
    
    # Log transaction
    await db.loyalty_transactions.insert_one({
        "id": str(uuid.uuid4()),
        "customer_id": transaction.customer_id,
        "points": transaction.points,
        "type": "earn",
        "sale_id": transaction.sale_id,
        "notes": transaction.notes or "",
        "balance_after": new_points,
        "created_at": now,
        "created_by": user.get("name", "")
    })
    
    return {"message": f"تم إضافة {transaction.points} نقطة", "new_balance": new_points}

@api_router.post("/loyalty/redeem")
async def redeem_loyalty_points(transaction: LoyaltyTransaction, user: dict = Depends(require_tenant)):
    """Redeem loyalty points"""
    customer = await db.customers.find_one({"id": transaction.customer_id})
    if not customer:
        raise HTTPException(status_code=404, detail="العميل غير موجود")
    
    current_points = customer.get("loyalty_points", 0)
    
    # Check minimum redeem
    settings = await db.loyalty_settings.find_one({"id": "global"}, {"_id": 0})
    min_redeem = settings.get("min_redeem_points", 100) if settings else 100
    
    if transaction.points > current_points:
        raise HTTPException(status_code=400, detail="رصيد النقاط غير كافي")
    
    if transaction.points < min_redeem:
        raise HTTPException(status_code=400, detail=f"الحد الأدنى للاسترداد {min_redeem} نقطة")
    
    now = datetime.now(timezone.utc).isoformat()
    new_points = current_points - transaction.points
    
    # Update customer points
    await db.customers.update_one(
        {"id": transaction.customer_id},
        {"$set": {"loyalty_points": new_points}}
    )
    
    # Log transaction
    points_value = settings.get("points_value", 0.1) if settings else 0.1
    discount_amount = transaction.points * points_value
    
    await db.loyalty_transactions.insert_one({
        "id": str(uuid.uuid4()),
        "customer_id": transaction.customer_id,
        "points": -transaction.points,
        "type": "redeem",
        "sale_id": transaction.sale_id,
        "notes": transaction.notes or f"خصم {discount_amount} دج",
        "balance_after": new_points,
        "created_at": now,
        "created_by": user.get("name", "")
    })
    
    return {
        "message": f"تم استرداد {transaction.points} نقطة",
        "discount_amount": discount_amount,
        "new_balance": new_points
    }

# ============ SMS MARKETING ============

class SMSCampaign(BaseModel):
    name: str
    message: str
    target: str  # all, customers_with_debt, inactive, custom
    customer_ids: Optional[List[str]] = []
    scheduled_at: Optional[str] = None

@api_router.get("/marketing/sms/campaigns")
async def get_sms_campaigns(admin: dict = Depends(get_tenant_admin)):
    """Get all SMS campaigns"""
    campaigns = await db.sms_campaigns.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return campaigns

@api_router.post("/marketing/sms/campaigns")
async def create_sms_campaign(campaign: SMSCampaign, admin: dict = Depends(get_tenant_admin)):
    """Create a new SMS campaign (MOCKED)"""
    now = datetime.now(timezone.utc).isoformat()
    
    # Determine target customers
    if campaign.target == "all":
        customers = await db.customers.find({"phone": {"$ne": ""}}, {"_id": 0, "id": 1, "phone": 1, "name": 1}).to_list(1000)
    elif campaign.target == "customers_with_debt":
        customers = await db.customers.find({"balance": {"$gt": 0}, "phone": {"$ne": ""}}, {"_id": 0, "id": 1, "phone": 1, "name": 1}).to_list(1000)
    elif campaign.target == "inactive":
        # Customers who haven't purchased in 30 days
        thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        active_customer_ids = await db.sales.distinct("customer_id", {"created_at": {"$gte": thirty_days_ago}})
        customers = await db.customers.find(
            {"id": {"$nin": active_customer_ids}, "phone": {"$ne": ""}},
            {"_id": 0, "id": 1, "phone": 1, "name": 1}
        ).to_list(1000)
    else:  # custom
        customers = await db.customers.find(
            {"id": {"$in": campaign.customer_ids}, "phone": {"$ne": ""}},
            {"_id": 0, "id": 1, "phone": 1, "name": 1}
        ).to_list(1000)
    
    campaign_doc = {
        "id": str(uuid.uuid4()),
        "name": campaign.name,
        "message": campaign.message,
        "target": campaign.target,
        "recipients_count": len(customers),
        "status": "pending" if campaign.scheduled_at else "sent",
        "scheduled_at": campaign.scheduled_at,
        "sent_at": now if not campaign.scheduled_at else None,
        "created_at": now,
        "created_by": admin.get("name", "")
    }
    
    await db.sms_campaigns.insert_one(campaign_doc)
    
    # MOCKED - In production, actually send SMS
    return {
        "success": True,
        "message": f"تم إنشاء الحملة وإرسالها لـ {len(customers)} عميل (وضع المحاكاة)",
        "campaign_id": campaign_doc["id"],
        "recipients_count": len(customers)
    }

# ============ INVOICES ============

class InvoiceTemplate(BaseModel):
    name: str
    type: str  # simple, detailed, thermal
    header_text: str = ""
    footer_text: str = ""
    show_logo: bool = True
    show_qr: bool = False

@api_router.get("/invoices/templates")
async def get_invoice_templates(user: dict = Depends(require_tenant)):
    """Get all invoice templates"""
    templates = await db.invoice_templates.find({}, {"_id": 0}).to_list(20)
    
    if not templates:
        # Create default templates
        default_templates = [
            {
                "id": "simple",
                "name": "فاتورة بسيطة",
                "name_fr": "Facture simple",
                "type": "simple",
                "header_text": "",
                "footer_text": "شكراً لتعاملكم معنا",
                "show_logo": True,
                "show_qr": False,
                "is_default": True
            },
            {
                "id": "detailed",
                "name": "فاتورة تفصيلية",
                "name_fr": "Facture détaillée",
                "type": "detailed",
                "header_text": "",
                "footer_text": "",
                "show_logo": True,
                "show_qr": True,
                "is_default": False
            },
            {
                "id": "thermal",
                "name": "فاتورة حرارية",
                "name_fr": "Ticket thermique",
                "type": "thermal",
                "header_text": "",
                "footer_text": "",
                "show_logo": False,
                "show_qr": False,
                "is_default": False
            }
        ]
        await db.invoice_templates.insert_many(default_templates)
        templates = default_templates
    
    return templates

@api_router.post("/invoices/generate/{sale_id}")
async def generate_invoice(sale_id: str, template_id: str = "simple", user: dict = Depends(require_tenant)):
    """Generate invoice for a sale"""
    sale = await db.sales.find_one({"id": sale_id}, {"_id": 0})
    if not sale:
        raise HTTPException(status_code=404, detail="البيع غير موجود")
    
    template = await db.invoice_templates.find_one({"id": template_id}, {"_id": 0})
    branding = await db.branding_settings.find_one({"id": "global"}, {"_id": 0})
    
    # Get customer info if exists
    customer = None
    if sale.get("customer_id"):
        customer = await db.customers.find_one({"id": sale["customer_id"]}, {"_id": 0})
    
    invoice_data = {
        "invoice_number": f"INV-{sale_id[:8].upper()}",
        "date": sale.get("created_at", ""),
        "business_name": branding.get("business_name", "NT") if branding else "NT",
        "logo_url": branding.get("logo_url", "") if branding else "",
        "customer": {
            "name": customer.get("name", "") if customer else sale.get("customer_name", ""),
            "phone": customer.get("phone", "") if customer else "",
            "address": customer.get("address", "") if customer else ""
        },
        "items": sale.get("items", []),
        "subtotal": sale.get("total", 0),
        "discount": sale.get("discount", 0),
        "total": sale.get("total", 0),
        "paid": sale.get("paid_amount", 0),
        "remaining": sale.get("remaining", 0),
        "payment_method": sale.get("payment_method", ""),
        "template": template,
        "header_text": template.get("header_text", "") if template else "",
        "footer_text": template.get("footer_text", "شكراً لتعاملكم معنا") if template else ""
    }
    
    return invoice_data

# ============ PAYMENT GATEWAYS (MOCKED) ============

class PaymentGatewaySettings(BaseModel):
    gateway: str  # cib, dahabia, baridimob
    enabled: bool = False
    merchant_id: str = ""
    api_key: str = ""
    terminal_id: str = ""

ALGERIAN_PAYMENT_GATEWAYS = [
    {"id": "cib", "name": "CIB", "name_ar": "البطاقة البنكية CIB", "type": "card"},
    {"id": "dahabia", "name": "Dahabia", "name_ar": "بطاقة الذهبية", "type": "card"},
    {"id": "baridimob", "name": "BaridiMob", "name_ar": "بريدي موب", "type": "mobile"}
]

@api_router.get("/payments/gateways")
async def get_payment_gateways(admin: dict = Depends(get_tenant_admin)):
    """Get available payment gateways"""
    settings = await db.payment_gateways.find({}, {"_id": 0}).to_list(10)
    
    result = []
    for gateway in ALGERIAN_PAYMENT_GATEWAYS:
        setting = next((s for s in settings if s.get("gateway") == gateway["id"]), None)
        result.append({
            **gateway,
            "enabled": setting.get("enabled", False) if setting else False,
            "configured": bool(setting.get("merchant_id")) if setting else False
        })
    
    return result

@api_router.put("/payments/gateways/{gateway_id}")
async def update_payment_gateway(gateway_id: str, settings: PaymentGatewaySettings, admin: dict = Depends(get_tenant_admin)):
    """Update payment gateway settings"""
    await db.payment_gateways.update_one(
        {"gateway": gateway_id},
        {"$set": settings.model_dump()},
        upsert=True
    )
    return {"message": "تم تحديث إعدادات بوابة الدفع"}

# ============ SMS REMINDER SYSTEM ============

class SMSReminderRequest(BaseModel):
    customer_ids: List[str]  # قائمة معرفات الزبائن
    message_template: Optional[str] = None  # قالب الرسالة المخصص

class SMSSettingsUpdate(BaseModel):
    auto_reminder_enabled: bool = False
    reminder_frequency: Literal["daily", "weekly", "monthly"] = "weekly"
    reminder_day: int = 1  # 1-7 للأسبوعي، 1-28 للشهري
    reminder_time: str = "09:00"
    min_debt_amount: float = 100  # الحد الأدنى للدين لإرسال تذكير
    message_template: str = "السلام عليكم {customer_name}، نذكركم بأن لديكم مبلغ {debt_amount} دج مستحق. شكراً لتعاملكم معنا."

# Default SMS settings
DEFAULT_SMS_SETTINGS = {
    "auto_reminder_enabled": False,
    "reminder_frequency": "weekly",
    "reminder_day": 1,
    "reminder_time": "09:00",
    "min_debt_amount": 100,
    "message_template": "السلام عليكم {customer_name}، نذكركم بأن لديكم مبلغ {debt_amount} دج مستحق. شكراً لتعاملكم معنا - NT"
}

async def send_sms_mock(phone: str, message: str) -> dict:
    """
    MOCKED SMS sending function
    Replace this with actual SMS provider integration
    Supported providers: SMS Algérie, Mobilzone, etc.
    """
    # Simulate SMS sending
    import random
    success = random.random() > 0.1  # 90% success rate simulation
    
    return {
        "success": success,
        "phone": phone,
        "message_length": len(message),
        "provider": "MOCKED",
        "message_id": str(uuid.uuid4()) if success else None,
        "error": None if success else "Simulated failure"
    }

@api_router.get("/sms/settings")
async def get_sms_settings(admin: dict = Depends(get_tenant_admin)):
    """Get SMS reminder settings"""
    settings = await db.sms_settings.find_one({"id": "global"}, {"_id": 0})
    if not settings:
        settings = {**DEFAULT_SMS_SETTINGS, "id": "global"}
        await db.sms_settings.insert_one(settings)
        # Return without _id
        settings = {k: v for k, v in settings.items() if k != "_id"}
    return settings

@api_router.put("/sms/settings")
async def update_sms_settings(settings: SMSSettingsUpdate, admin: dict = Depends(get_tenant_admin)):
    """Update SMS reminder settings"""
    update_data = settings.model_dump()
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.sms_settings.update_one(
        {"id": "global"},
        {"$set": update_data},
        upsert=True
    )
    
    return {"success": True, "message": "Settings updated"}

@api_router.post("/sms/send-reminder")
async def send_debt_reminder(request: SMSReminderRequest, user: dict = Depends(require_tenant)):
    """Send SMS reminder to selected customers"""
    settings = await db.sms_settings.find_one({"id": "global"}, {"_id": 0})
    if not settings:
        settings = DEFAULT_SMS_SETTINGS
    
    template = request.message_template or settings.get("message_template", DEFAULT_SMS_SETTINGS["message_template"])
    
    results = []
    for customer_id in request.customer_ids:
        # Get customer info
        customer = await db.customers.find_one({"id": customer_id}, {"_id": 0})
        if not customer:
            results.append({"customer_id": customer_id, "success": False, "error": "Customer not found"})
            continue
        
        if not customer.get("phone"):
            results.append({"customer_id": customer_id, "success": False, "error": "No phone number"})
            continue
        
        # Get customer debt
        debt_pipeline = [
            {"$match": {"customer_id": customer_id, "debt_amount": {"$gt": 0}}},
            {"$group": {"_id": None, "total": {"$sum": "$debt_amount"}}}
        ]
        debt_result = await db.sales.aggregate(debt_pipeline).to_list(1)
        total_debt = debt_result[0]["total"] if debt_result else 0
        
        if total_debt <= 0:
            results.append({"customer_id": customer_id, "success": False, "error": "No debt"})
            continue
        
        # Format message
        message = template.format(
            customer_name=customer.get("name", ""),
            debt_amount=f"{total_debt:,.0f}",
            phone=customer.get("phone", "")
        )
        
        # Send SMS (MOCKED)
        sms_result = await send_sms_mock(customer["phone"], message)
        
        # Log the SMS
        sms_log = {
            "id": str(uuid.uuid4()),
            "customer_id": customer_id,
            "customer_name": customer.get("name", ""),
            "phone": customer.get("phone", ""),
            "message": message,
            "debt_amount": total_debt,
            "status": "sent" if sms_result["success"] else "failed",
            "provider_response": sms_result,
            "sent_by": user.get("name", ""),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.sms_logs.insert_one(sms_log)
        
        results.append({
            "customer_id": customer_id,
            "customer_name": customer.get("name", ""),
            "phone": customer.get("phone", ""),
            "success": sms_result["success"],
            "error": sms_result.get("error")
        })
    
    success_count = sum(1 for r in results if r.get("success"))
    return {
        "total": len(request.customer_ids),
        "success": success_count,
        "failed": len(request.customer_ids) - success_count,
        "results": results
    }

@api_router.post("/sms/send-bulk-reminder")
async def send_bulk_debt_reminder(user: dict = Depends(require_tenant), min_debt: float = 0):
    """Send SMS reminder to all customers with debt"""
    settings = await db.sms_settings.find_one({"id": "global"}, {"_id": 0})
    if not settings:
        settings = DEFAULT_SMS_SETTINGS
    
    min_amount = min_debt if min_debt > 0 else settings.get("min_debt_amount", 100)
    
    # Get all customers with debt above minimum
    pipeline = [
        {"$match": {"debt_amount": {"$gt": 0}}},
        {"$group": {
            "_id": "$customer_id",
            "total_debt": {"$sum": "$debt_amount"}
        }},
        {"$match": {"total_debt": {"$gte": min_amount}}}
    ]
    
    debts = await db.sales.aggregate(pipeline).to_list(1000)
    customer_ids = [d["_id"] for d in debts if d["_id"]]
    
    if not customer_ids:
        return {"total": 0, "success": 0, "failed": 0, "results": [], "message": "No customers with debt found"}
    
    # Use the single reminder endpoint
    request = SMSReminderRequest(customer_ids=customer_ids)
    return await send_debt_reminder(request, user)

@api_router.get("/sms/logs")
async def get_sms_logs(
    limit: int = 50,
    customer_id: Optional[str] = None,
    user: dict = Depends(require_tenant)
):
    """Get SMS sending history"""
    query = {}
    if customer_id:
        query["customer_id"] = customer_id
    
    logs = await db.sms_logs.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    
    # Stats
    total_sent = await db.sms_logs.count_documents({"status": "sent"})
    total_failed = await db.sms_logs.count_documents({"status": "failed"})
    
    return {
        "logs": logs,
        "stats": {
            "total_sent": total_sent,
            "total_failed": total_failed
        }
    }

@api_router.get("/sms/templates")
async def get_sms_templates():
    """Get predefined SMS templates"""
    return {
        "templates": [
            {
                "id": "reminder_friendly",
                "name_ar": "تذكير ودي",
                "name_en": "Friendly Reminder",
                "template": "السلام عليكم {customer_name}، نذكركم بأن لديكم مبلغ {debt_amount} دج مستحق. شكراً لتعاملكم معنا."
            },
            {
                "id": "reminder_formal",
                "name_ar": "تذكير رسمي",
                "name_en": "Formal Reminder",
                "template": "عزيزنا {customer_name}، نود إعلامكم بوجود مستحقات بقيمة {debt_amount} دج. نرجو التسديد في أقرب وقت."
            },
            {
                "id": "reminder_urgent",
                "name_ar": "تذكير عاجل",
                "name_en": "Urgent Reminder",
                "template": "تنبيه: {customer_name}، لديكم مبلغ {debt_amount} دج متأخر السداد. يرجى التواصل معنا."
            },
            {
                "id": "payment_thanks",
                "name_ar": "شكر على الدفع",
                "name_en": "Payment Thanks",
                "template": "شكراً {customer_name} على سداد مستحقاتكم. نقدر تعاملكم معنا - NT"
            }
        ]
    }

# ============ ADVANCED ROLES AND PERMISSIONS ============

@api_router.get("/permissions/roles")
async def get_all_roles():
    """Get all available roles with their default permissions and descriptions"""
    return {
        "roles": list(DEFAULT_PERMISSIONS.keys()),
        "default_permissions": DEFAULT_PERMISSIONS,
        "role_descriptions": ROLE_DESCRIPTIONS,
        "permission_categories": PERMISSION_CATEGORIES
    }

@api_router.get("/permissions/categories")
async def get_permission_categories():
    """Get permission categories for UI grouping"""
    return PERMISSION_CATEGORIES

@api_router.get("/permissions/role/{role_name}")
async def get_role_permissions(role_name: str):
    """Get permissions for a specific role"""
    if role_name not in DEFAULT_PERMISSIONS:
        raise HTTPException(status_code=404, detail="Role not found")
    
    return {
        "role": role_name,
        "description": ROLE_DESCRIPTIONS.get(role_name, {"ar": role_name, "fr": role_name}),
        "permissions": DEFAULT_PERMISSIONS[role_name]
    }

# ============ FILE UPLOAD ============

@api_router.post("/upload/image")
async def upload_image(file: UploadFile = File(...), user: dict = Depends(require_tenant)):
    """Upload an image file"""
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/webp", "image/gif"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type. Only images are allowed.")
    
    # Generate unique filename
    file_ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    unique_filename = f"{uuid.uuid4()}.{file_ext}"
    file_path = UPLOAD_DIR / unique_filename
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Return URL (relative to static)
        return {"url": f"/api/static/uploads/{unique_filename}", "filename": unique_filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

# ============ PERMISSIONS SYSTEM ============

@api_router.get("/permissions/roles")
async def get_available_roles():
    """Get all available roles and their default permissions"""
    return {
        "roles": ["admin", "manager", "user"],
        "default_permissions": DEFAULT_PERMISSIONS
    }

@api_router.get("/users/{user_id}/permissions")
async def get_user_permissions(user_id: str, admin: dict = Depends(get_tenant_admin)):
    """Get permissions for a specific user"""
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # If user has custom permissions, return them; otherwise return role defaults
    permissions = user.get("permissions") or DEFAULT_PERMISSIONS.get(user.get("role", "user"), {})
    return {
        "user_id": user_id,
        "role": user.get("role", "user"),
        "permissions": permissions,
        "is_custom": bool(user.get("permissions"))
    }

@api_router.put("/users/{user_id}/permissions")
async def update_user_permissions(user_id: str, permissions: dict, admin: dict = Depends(get_tenant_admin)):
    """Update permissions for a specific user"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"permissions": permissions}}
    )
    
    return {"success": True, "message": "Permissions updated"}

@api_router.put("/users/{user_id}/reset-permissions")
async def reset_user_permissions(user_id: str, admin: dict = Depends(get_tenant_admin)):
    """Reset user permissions to role defaults"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db.users.update_one(
        {"id": user_id},
        {"$unset": {"permissions": ""}}
    )
    
    return {"success": True, "message": "Permissions reset to defaults"}

# ============ FACTORY RESET ============

@api_router.post("/system/factory-reset")
async def factory_reset(confirm_code: str, admin: dict = Depends(get_tenant_admin)):
    """Factory reset - Delete all data except admin user"""
    # Verify confirmation code
    if confirm_code != "RESET-ALL-DATA":
        raise HTTPException(status_code=400, detail="Invalid confirmation code")
    
    # Check if user has factory_reset permission
    user_permissions = admin.get("permissions") or DEFAULT_PERMISSIONS.get(admin.get("role", "user"), {})
    if not user_permissions.get("factory_reset", False):
        raise HTTPException(status_code=403, detail="No permission for factory reset")
    
    # Collections to clear
    collections_to_clear = [
        "products", "customers", "suppliers", "employees", 
        "sales", "purchases", "debts", "debt_payments",
        "transactions", "notifications", "sms_logs",
        "product_families", "api_keys", "recharges"
    ]
    
    deleted_counts = {}
    for collection in collections_to_clear:
        result = await db[collection].delete_many({})
        deleted_counts[collection] = result.deleted_count
    
    # Reset cash boxes to zero
    await db.cash_boxes.update_many({}, {"$set": {"balance": 0}})
    
    # Keep admin user, delete others
    await db.users.delete_many({"role": {"$ne": "admin"}})
    
    # Log the reset
    await db.system_logs.insert_one({
        "id": str(uuid.uuid4()),
        "action": "factory_reset",
        "performed_by": admin.get("name", ""),
        "deleted_counts": deleted_counts,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "success": True,
        "message": "Factory reset completed",
        "deleted_counts": deleted_counts
    }

@api_router.get("/system/stats")
async def get_system_stats(admin: dict = Depends(get_tenant_admin)):
    """Get system statistics for factory reset preview"""
    stats = {
        "products": await db.products.count_documents({}),
        "customers": await db.customers.count_documents({}),
        "suppliers": await db.suppliers.count_documents({}),
        "employees": await db.employees.count_documents({}),
        "sales": await db.sales.count_documents({}),
        "users": await db.users.count_documents({}),
        "product_families": await db.product_families.count_documents({}),
        "recharges": await db.recharges.count_documents({})
    }
    return stats

# ============ BULK PRICE UPDATE ============

class BulkPriceUpdateRequest(BaseModel):
    product_ids: Optional[List[str]] = None  # None = all products
    family_id: Optional[str] = None  # Filter by family
    update_type: Literal["percentage", "fixed", "set"]  # نسبة مئوية، مبلغ ثابت، تحديد قيمة
    price_field: Literal["purchase_price", "wholesale_price", "retail_price", "all"]
    value: float
    round_to: int = 0  # Round to nearest (0 = no rounding, 10 = nearest 10, etc.)

@api_router.post("/products/bulk-price-update")
async def bulk_price_update(request: BulkPriceUpdateRequest, admin: dict = Depends(get_tenant_admin)):
    """Update prices for multiple products at once"""
    
    # Build query
    query = {}
    if request.product_ids:
        query["id"] = {"$in": request.product_ids}
    if request.family_id:
        query["family_id"] = request.family_id
    
    # Get products
    products = await db.products.find(query, {"_id": 0}).to_list(10000)
    
    if not products:
        return {"success": False, "message": "No products found", "updated_count": 0}
    
    price_fields = ["purchase_price", "wholesale_price", "retail_price"] if request.price_field == "all" else [request.price_field]
    
    updated_count = 0
    updates_log = []
    
    for product in products:
        update_data = {}
        
        for field in price_fields:
            old_price = product.get(field, 0)
            new_price = old_price
            
            if request.update_type == "percentage":
                # Increase/decrease by percentage
                new_price = old_price * (1 + request.value / 100)
            elif request.update_type == "fixed":
                # Add/subtract fixed amount
                new_price = old_price + request.value
            elif request.update_type == "set":
                # Set to specific value
                new_price = request.value
            
            # Round if needed
            if request.round_to > 0:
                new_price = round(new_price / request.round_to) * request.round_to
            
            # Ensure price is not negative
            new_price = max(0, new_price)
            
            update_data[field] = new_price
        
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        await db.products.update_one({"id": product["id"]}, {"$set": update_data})
        updated_count += 1
        
        updates_log.append({
            "product_id": product["id"],
            "product_name": product.get("name_ar", product.get("name_en", "")),
            "old_prices": {f: product.get(f, 0) for f in price_fields},
            "new_prices": {f: update_data[f] for f in price_fields}
        })
    
    # Log the bulk update
    await db.system_logs.insert_one({
        "id": str(uuid.uuid4()),
        "action": "bulk_price_update",
        "performed_by": admin.get("name", ""),
        "update_type": request.update_type,
        "value": request.value,
        "updated_count": updated_count,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "success": True,
        "updated_count": updated_count,
        "updates": updates_log[:10]  # Return first 10 as sample
    }

@api_router.get("/products/price-preview")
async def preview_price_update(
    update_type: str,
    price_field: str,
    value: float,
    family_id: Optional[str] = None,
    round_to: int = 0,
    admin: dict = Depends(get_tenant_admin)
):
    """Preview price changes before applying"""
    query = {}
    if family_id:
        query["family_id"] = family_id
    
    products = await db.products.find(query, {"_id": 0}).limit(20).to_list(20)
    
    previews = []
    for product in products:
        price_fields = ["purchase_price", "wholesale_price", "retail_price"] if price_field == "all" else [price_field]
        
        preview = {
            "id": product["id"],
            "name": product.get("name_ar", product.get("name_en", "")),
            "changes": {}
        }
        
        for field in price_fields:
            old_price = product.get(field, 0)
            new_price = old_price
            
            if update_type == "percentage":
                new_price = old_price * (1 + value / 100)
            elif update_type == "fixed":
                new_price = old_price + value
            elif update_type == "set":
                new_price = value
            
            if round_to > 0:
                new_price = round(new_price / round_to) * round_to
            
            new_price = max(0, new_price)
            
            preview["changes"][field] = {
                "old": old_price,
                "new": new_price,
                "diff": new_price - old_price
            }
        
        previews.append(preview)
    
    return {
        "preview_count": len(previews),
        "total_products": await db.products.count_documents(query),
        "previews": previews
    }

# ============ PRODUCT FAMILIES ROUTES ============

@api_router.post("/product-families", response_model=ProductFamilyResponse)
async def create_product_family(family: ProductFamilyCreate, admin: dict = Depends(get_tenant_admin)):
    family_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    # Get parent name if exists
    parent_name = ""
    if family.parent_id:
        parent = await db.product_families.find_one({"id": family.parent_id}, {"_id": 0, "name_ar": 1})
        if parent:
            parent_name = parent["name_ar"]
    
    family_doc = {
        "id": family_id,
        "name_en": family.name_en,
        "name_ar": family.name_ar,
        "description_en": family.description_en or "",
        "description_ar": family.description_ar or "",
        "parent_id": family.parent_id or "",
        "parent_name": parent_name,
        "product_count": 0,
        "created_at": now
    }
    await db.product_families.insert_one(family_doc)
    return ProductFamilyResponse(**family_doc)

@api_router.get("/product-families", response_model=List[ProductFamilyResponse])
async def get_product_families(user: dict = Depends(require_tenant)):
    families = await db.product_families.find({}, {"_id": 0}).to_list(1000)
    
    # Update product counts
    for family in families:
        count = await db.products.count_documents({"family_id": family["id"]})
        family["product_count"] = count
    
    return [ProductFamilyResponse(**f) for f in families]

@api_router.get("/product-families/{family_id}", response_model=ProductFamilyResponse)
async def get_product_family(family_id: str, user: dict = Depends(require_tenant)):
    family = await db.product_families.find_one({"id": family_id}, {"_id": 0})
    if not family:
        raise HTTPException(status_code=404, detail="Product family not found")
    
    # Update product count
    count = await db.products.count_documents({"family_id": family_id})
    family["product_count"] = count
    
    return ProductFamilyResponse(**family)

@api_router.put("/product-families/{family_id}", response_model=ProductFamilyResponse)
async def update_product_family(family_id: str, updates: ProductFamilyUpdate, admin: dict = Depends(get_tenant_admin)):
    family = await db.product_families.find_one({"id": family_id})
    if not family:
        raise HTTPException(status_code=404, detail="Product family not found")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    
    # Update parent name if parent_id changed
    if "parent_id" in update_data and update_data["parent_id"]:
        parent = await db.product_families.find_one({"id": update_data["parent_id"]}, {"_id": 0, "name_ar": 1})
        update_data["parent_name"] = parent["name_ar"] if parent else ""
    elif "parent_id" in update_data and not update_data["parent_id"]:
        update_data["parent_name"] = ""
    
    if update_data:
        await db.product_families.update_one({"id": family_id}, {"$set": update_data})
    
    updated = await db.product_families.find_one({"id": family_id}, {"_id": 0})
    count = await db.products.count_documents({"family_id": family_id})
    updated["product_count"] = count
    
    return ProductFamilyResponse(**updated)

@api_router.delete("/product-families/{family_id}")
async def delete_product_family(family_id: str, admin: dict = Depends(get_tenant_admin)):
    # Check if family has products
    product_count = await db.products.count_documents({"family_id": family_id})
    if product_count > 0:
        raise HTTPException(status_code=400, detail=f"Cannot delete family with {product_count} products")
    
    # Check if family has children
    child_count = await db.product_families.count_documents({"parent_id": family_id})
    if child_count > 0:
        raise HTTPException(status_code=400, detail=f"Cannot delete family with {child_count} sub-families")
    
    result = await db.product_families.delete_one({"id": family_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product family not found")
    return {"message": "Product family deleted successfully"}

@api_router.get("/product-families/{family_id}/products", response_model=List[ProductResponse])
async def get_family_products(family_id: str, user: dict = Depends(require_tenant)):
    """Get all products in a specific family"""
    products = await db.products.find({"family_id": family_id}, {"_id": 0}).to_list(1000)
    
    # Add family names
    for product in products:
        if product.get("family_id"):
            family = await db.product_families.find_one({"id": product["family_id"]}, {"_id": 0, "name_ar": 1})
            product["family_name"] = family["name_ar"] if family else ""
        else:
            product["family_name"] = ""
    
    return [ProductResponse(**p) for p in products]

# ============ CUSTOMER & SUPPLIER FAMILIES ============

class CustomerFamilyCreate(BaseModel):
    name: str
    description: Optional[str] = ""

class CustomerFamilyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class CustomerFamilyResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    description: str
    customer_count: int = 0
    created_at: str

class SupplierFamilyCreate(BaseModel):
    name: str
    description: Optional[str] = ""

class SupplierFamilyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class SupplierFamilyResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    description: str
    supplier_count: int = 0
    created_at: str

# Customer Families CRUD
@api_router.post("/customer-families", response_model=CustomerFamilyResponse)
async def create_customer_family(family: CustomerFamilyCreate, admin: dict = Depends(get_tenant_admin)):
    family_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    family_doc = {
        "id": family_id,
        "name": family.name,
        "description": family.description or "",
        "customer_count": 0,
        "created_at": now
    }
    
    await db.customer_families.insert_one(family_doc)
    return CustomerFamilyResponse(**family_doc)

@api_router.get("/customer-families", response_model=List[CustomerFamilyResponse])
async def get_customer_families(user: dict = Depends(require_tenant)):
    families = await db.customer_families.find({}, {"_id": 0}).to_list(100)
    
    # Update customer counts
    for family in families:
        count = await db.customers.count_documents({"family_id": family["id"]})
        family["customer_count"] = count
    
    return [CustomerFamilyResponse(**f) for f in families]

@api_router.get("/customer-families/{family_id}", response_model=CustomerFamilyResponse)
async def get_customer_family(family_id: str, user: dict = Depends(require_tenant)):
    family = await db.customer_families.find_one({"id": family_id}, {"_id": 0})
    if not family:
        raise HTTPException(status_code=404, detail="عائلة الزبائن غير موجودة")
    
    count = await db.customers.count_documents({"family_id": family_id})
    family["customer_count"] = count
    
    return CustomerFamilyResponse(**family)

@api_router.put("/customer-families/{family_id}", response_model=CustomerFamilyResponse)
async def update_customer_family(family_id: str, updates: CustomerFamilyUpdate, admin: dict = Depends(get_tenant_admin)):
    family = await db.customer_families.find_one({"id": family_id})
    if not family:
        raise HTTPException(status_code=404, detail="عائلة الزبائن غير موجودة")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    if update_data:
        await db.customer_families.update_one({"id": family_id}, {"$set": update_data})
    
    updated = await db.customer_families.find_one({"id": family_id}, {"_id": 0})
    count = await db.customers.count_documents({"family_id": family_id})
    updated["customer_count"] = count
    
    return CustomerFamilyResponse(**updated)

@api_router.delete("/customer-families/{family_id}")
async def delete_customer_family(family_id: str, admin: dict = Depends(get_tenant_admin)):
    count = await db.customers.count_documents({"family_id": family_id})
    if count > 0:
        raise HTTPException(status_code=400, detail=f"لا يمكن حذف عائلة بها {count} زبون")
    
    result = await db.customer_families.delete_one({"id": family_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="عائلة الزبائن غير موجودة")
    return {"message": "تم حذف عائلة الزبائن بنجاح"}

# Supplier Families CRUD
@api_router.post("/supplier-families", response_model=SupplierFamilyResponse)
async def create_supplier_family(family: SupplierFamilyCreate, admin: dict = Depends(get_tenant_admin)):
    family_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    family_doc = {
        "id": family_id,
        "name": family.name,
        "description": family.description or "",
        "supplier_count": 0,
        "created_at": now
    }
    
    await db.supplier_families.insert_one(family_doc)
    return SupplierFamilyResponse(**family_doc)

@api_router.get("/supplier-families", response_model=List[SupplierFamilyResponse])
async def get_supplier_families(user: dict = Depends(require_tenant)):
    families = await db.supplier_families.find({}, {"_id": 0}).to_list(100)
    
    # Update supplier counts
    for family in families:
        count = await db.suppliers.count_documents({"family_id": family["id"]})
        family["supplier_count"] = count
    
    return [SupplierFamilyResponse(**f) for f in families]

@api_router.get("/supplier-families/{family_id}", response_model=SupplierFamilyResponse)
async def get_supplier_family(family_id: str, user: dict = Depends(require_tenant)):
    family = await db.supplier_families.find_one({"id": family_id}, {"_id": 0})
    if not family:
        raise HTTPException(status_code=404, detail="عائلة الموردين غير موجودة")
    
    count = await db.suppliers.count_documents({"family_id": family_id})
    family["supplier_count"] = count
    
    return SupplierFamilyResponse(**family)

@api_router.put("/supplier-families/{family_id}", response_model=SupplierFamilyResponse)
async def update_supplier_family(family_id: str, updates: SupplierFamilyUpdate, admin: dict = Depends(get_tenant_admin)):
    family = await db.supplier_families.find_one({"id": family_id})
    if not family:
        raise HTTPException(status_code=404, detail="عائلة الموردين غير موجودة")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    if update_data:
        await db.supplier_families.update_one({"id": family_id}, {"$set": update_data})
    
    updated = await db.supplier_families.find_one({"id": family_id}, {"_id": 0})
    count = await db.suppliers.count_documents({"family_id": family_id})
    updated["supplier_count"] = count
    
    return SupplierFamilyResponse(**updated)

@api_router.delete("/supplier-families/{family_id}")
async def delete_supplier_family(family_id: str, admin: dict = Depends(get_tenant_admin)):
    count = await db.suppliers.count_documents({"family_id": family_id})
    if count > 0:
        raise HTTPException(status_code=400, detail=f"لا يمكن حذف عائلة بها {count} مورد")
    
    result = await db.supplier_families.delete_one({"id": family_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="عائلة الموردين غير موجودة")
    return {"message": "تم حذف عائلة الموردين بنجاح"}

# ============ WHATSAPP NOTIFICATIONS ============

class WhatsAppSettings(BaseModel):
    enabled: bool = False
    phone_number_id: Optional[str] = None
    access_token: Optional[str] = None
    business_account_id: Optional[str] = None

class WhatsAppMessage(BaseModel):
    phone: str
    message: str

# Status messages in Arabic
REPAIR_STATUS_MESSAGES = {
    "received": "مرحباً {customer_name}! تم استلام جهازك ({device}) للصيانة. رقم التذكرة: {ticket_number}. سنقوم بإشعارك عند أي تحديث.",
    "diagnosing": "تحديث الصيانة #{ticket_number}: جاري فحص جهازك ({device}) لتحديد العطل.",
    "waiting_parts": "تحديث الصيانة #{ticket_number}: جهازك ({device}) بحاجة لقطع غيار. سنقوم بإعلامك فور توفرها.",
    "in_progress": "تحديث الصيانة #{ticket_number}: جاري إصلاح جهازك ({device}). الوقت المتوقع: {estimated_days} أيام.",
    "completed": "🎉 أخبار سارة! تم إصلاح جهازك ({device}) بنجاح. رقم التذكرة: {ticket_number}. يمكنك استلامه الآن. التكلفة: {cost} دج",
    "delivered": "شكراً لثقتك بنا! تم تسليم جهازك ({device}). نتمنى لك يوماً سعيداً! 🙏",
    "cancelled": "تم إلغاء طلب الصيانة #{ticket_number}. للاستفسار يرجى التواصل معنا."
}

@api_router.get("/whatsapp/settings")
async def get_whatsapp_settings(user: dict = Depends(require_tenant)):
    """Get WhatsApp settings"""
    settings = await db.whatsapp_settings.find_one({}, {"_id": 0})
    if not settings:
        settings = {"enabled": False}
    # Don't expose access_token
    if "access_token" in settings:
        settings["access_token"] = "***" if settings["access_token"] else None
    return settings

@api_router.put("/whatsapp/settings")
async def update_whatsapp_settings(settings: WhatsAppSettings, user: dict = Depends(require_tenant)):
    """Update WhatsApp settings"""
    settings_data = settings.model_dump()
    settings_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    settings_data["updated_by"] = user["id"]
    
    await db.whatsapp_settings.update_one(
        {},
        {"$set": settings_data},
        upsert=True
    )
    return {"message": "تم تحديث إعدادات WhatsApp"}

@api_router.post("/whatsapp/send")
async def send_whatsapp_message(message: WhatsAppMessage, user: dict = Depends(require_tenant)):
    """Send a WhatsApp message"""
    settings = await db.whatsapp_settings.find_one({}, {"_id": 0})
    if not settings or not settings.get("enabled"):
        raise HTTPException(status_code=400, detail="WhatsApp غير مفعل")
    
    if not settings.get("access_token") or not settings.get("phone_number_id"):
        raise HTTPException(status_code=400, detail="إعدادات WhatsApp غير مكتملة")
    
    # Format phone number (remove leading 0 and add country code)
    phone = message.phone.strip()
    if phone.startswith("0"):
        phone = "213" + phone[1:]  # Algeria country code
    elif not phone.startswith("213"):
        phone = "213" + phone
    
    url = f"https://graph.facebook.com/v18.0/{settings['phone_number_id']}/messages"
    
    headers = {
        "Authorization": f"Bearer {settings['access_token']}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": phone,
        "type": "text",
        "text": {"body": message.message}
    }
    
    try:
        response = http_requests.post(url, json=payload, headers=headers)
        
        # Log the message
        await db.whatsapp_logs.insert_one({
            "id": str(uuid.uuid4()),
            "phone": phone,
            "message": message.message,
            "status": "sent" if response.status_code == 200 else "failed",
            "response_code": response.status_code,
            "response": response.text[:500] if response.text else None,
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "sent_by": user["id"]
        })
        
        if response.status_code == 200:
            return {"success": True, "message": "تم إرسال الرسالة"}
        else:
            return {"success": False, "error": response.text}
    except Exception as e:
        logger.error(f"WhatsApp send error: {str(e)}")
        return {"success": False, "error": str(e)}

@api_router.post("/whatsapp/notify-repair/{repair_id}")
async def notify_repair_status_change(repair_id: str, user: dict = Depends(require_tenant)):
    """Send WhatsApp notification for repair status change"""
    repair = await db.repairs.find_one({"id": repair_id}, {"_id": 0})
    if not repair:
        repair = await db.repairs.find_one({"ticket_number": repair_id}, {"_id": 0})
    if not repair:
        raise HTTPException(status_code=404, detail="طلب الصيانة غير موجود")
    
    settings = await db.whatsapp_settings.find_one({}, {"_id": 0})
    if not settings or not settings.get("enabled"):
        return {"success": False, "message": "WhatsApp غير مفعل"}
    
    status = repair.get("status", "received")
    message_template = REPAIR_STATUS_MESSAGES.get(status)
    
    if not message_template:
        return {"success": False, "message": "قالب الرسالة غير موجود"}
    
    # Format the message
    message = message_template.format(
        customer_name=repair.get("customer_name", "عميل"),
        device=f"{repair.get('device_brand', '')} {repair.get('device_model', '')}",
        ticket_number=repair.get("ticket_number", repair_id),
        estimated_days=repair.get("estimated_days", 1),
        cost=repair.get("final_cost") or repair.get("estimated_cost", 0)
    )
    
    # Send the message
    whatsapp_msg = WhatsAppMessage(phone=repair.get("customer_phone", ""), message=message)
    return await send_whatsapp_message(whatsapp_msg, user)

@api_router.get("/whatsapp/logs")
async def get_whatsapp_logs(
    limit: int = 50,
    user: dict = Depends(require_tenant)
):
    """Get WhatsApp message logs"""
    logs = await db.whatsapp_logs.find({}, {"_id": 0}).sort("sent_at", -1).limit(limit).to_list(limit)
    return logs

# ============ SPARE PARTS - PRODUCTS INTEGRATION ============

@api_router.post("/spare-parts/use-in-repair")
async def use_spare_part_in_repair(
    repair_id: str,
    part_id: str,
    quantity: int = 1,
    user: dict = Depends(require_tenant)
):
    """Use a spare part in a repair - deducts from inventory"""
    # Verify repair exists
    repair = await db.repairs.find_one({"id": repair_id}, {"_id": 0})
    if not repair:
        raise HTTPException(status_code=404, detail="طلب الصيانة غير موجود")
    
    # Verify spare part exists and has enough stock
    part = await db.spare_parts.find_one({"id": part_id}, {"_id": 0})
    if not part:
        raise HTTPException(status_code=404, detail="قطعة الغيار غير موجودة")
    
    if part.get("quantity", 0) < quantity:
        raise HTTPException(status_code=400, detail="الكمية غير كافية في المخزون")
    
    # Deduct from spare parts inventory
    new_qty = part["quantity"] - quantity
    await db.spare_parts.update_one(
        {"id": part_id},
        {"$set": {"quantity": new_qty, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Record the usage in repair
    usage_record = {
        "part_id": part_id,
        "part_name": part.get("name"),
        "quantity": quantity,
        "unit_price": part.get("sell_price", 0),
        "total_price": part.get("sell_price", 0) * quantity,
        "used_at": datetime.now(timezone.utc).isoformat(),
        "used_by": user["name"]
    }
    
    await db.repairs.update_one(
        {"id": repair_id},
        {
            "$push": {"parts_used": usage_record},
            "$inc": {"parts_cost": usage_record["total_price"]}
        }
    )
    
    # Also check if there's a linked product in main inventory
    if part.get("linked_product_id"):
        await db.products.update_one(
            {"id": part["linked_product_id"]},
            {"$inc": {"quantity": -quantity}}
        )
    
    return {
        "success": True,
        "message": f"تم استخدام {quantity} من {part['name']}",
        "remaining_stock": new_qty,
        "total_cost": usage_record["total_price"]
    }

@api_router.post("/spare-parts/link-to-product")
async def link_spare_part_to_product(
    part_id: str,
    product_id: str,
    user: dict = Depends(require_tenant)
):
    """Link a spare part to a main product for synchronized inventory"""
    # Verify both exist
    part = await db.spare_parts.find_one({"id": part_id}, {"_id": 0})
    if not part:
        raise HTTPException(status_code=404, detail="قطعة الغيار غير موجودة")
    
    product = await db.products.find_one({"id": product_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="المنتج غير موجود")
    
    # Link them
    await db.spare_parts.update_one(
        {"id": part_id},
        {"$set": {
            "linked_product_id": product_id,
            "linked_product_name": product.get("name"),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {
        "success": True,
        "message": f"تم ربط {part['name']} بالمنتج {product['name']}"
    }

@api_router.delete("/spare-parts/unlink-product/{part_id}")
async def unlink_spare_part_from_product(
    part_id: str,
    user: dict = Depends(require_tenant)
):
    """Remove link between spare part and product"""
    part = await db.spare_parts.find_one({"id": part_id}, {"_id": 0})
    if not part:
        raise HTTPException(status_code=404, detail="قطعة الغيار غير موجودة")
    
    await db.spare_parts.update_one(
        {"id": part_id},
        {"$unset": {"linked_product_id": "", "linked_product_name": ""}}
    )
    
    return {"success": True, "message": "تم إلغاء الربط"}

@api_router.post("/spare-parts/sync-inventory")
async def sync_spare_parts_with_products(user: dict = Depends(require_tenant)):
    """Sync spare parts inventory with linked products"""
    # Get all linked spare parts
    linked_parts = await db.spare_parts.find(
        {"linked_product_id": {"$exists": True}},
        {"_id": 0}
    ).to_list(1000)
    
    synced = 0
    for part in linked_parts:
        product = await db.products.find_one(
            {"id": part["linked_product_id"]},
            {"_id": 0, "quantity": 1}
        )
        if product:
            # Update spare part quantity to match product
            await db.spare_parts.update_one(
                {"id": part["id"]},
                {"$set": {"quantity": product.get("quantity", 0)}}
            )
            synced += 1
    
    return {"success": True, "synced_count": synced}

# ============ EMAIL REPORTS ============

class SessionReportEmail(BaseModel):
    recipient_email: EmailStr
    session_id: str
    report_data: dict

def generate_session_report_html(report: dict, language: str = 'ar') -> str:
    """Generate HTML email for session closing report"""
    
    def format_currency(amount):
        return f"{amount:,.2f}"
    
    currency = "دج" if language == 'ar' else "DA"
    
    # Determine difference color
    diff = report.get('cashDifference', 0)
    diff_color = '#22c55e' if diff >= 0 else '#ef4444'
    diff_sign = '+' if diff >= 0 else ''
    
    html = f"""
    <!DOCTYPE html>
    <html dir="rtl" lang="ar">
    <head>
        <meta charset="UTF-8">
    </head>
    <body style="font-family: 'Segoe UI', Tahoma, sans-serif; background-color: #f3f4f6; margin: 0; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #3b82f6, #1d4ed8); padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 24px;">📊 تقرير غلق الحصة</h1>
                <p style="color: rgba(255,255,255,0.9); margin-top: 10px;">
                    {datetime.fromisoformat(report.get('closedAt', '')).strftime('%Y-%m-%d %H:%M') if report.get('closedAt') else ''}
                </p>
            </div>
            
            <!-- Cash Summary -->
            <div style="padding: 20px;">
                <h2 style="color: #1f2937; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px; font-size: 18px;">💵 ملخص الصندوق</h2>
                <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                    <tr>
                        <td style="padding: 12px; background: #dbeafe; border-radius: 8px; margin: 5px;">
                            <span style="color: #6b7280; font-size: 12px;">رصيد الافتتاح</span><br>
                            <strong style="color: #2563eb; font-size: 18px;">{format_currency(report.get('openingCash', 0))} {currency}</strong>
                        </td>
                        <td style="padding: 12px; background: #dcfce7; border-radius: 8px; margin: 5px;">
                            <span style="color: #6b7280; font-size: 12px;">المبلغ المحصل</span><br>
                            <strong style="color: #16a34a; font-size: 18px;">{format_currency(report.get('totalCollected', 0))} {currency}</strong>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; background: #f3e8ff; border-radius: 8px; margin: 5px;">
                            <span style="color: #6b7280; font-size: 12px;">المتوقع في الصندوق</span><br>
                            <strong style="color: #9333ea; font-size: 18px;">{format_currency(report.get('expectedCash', 0))} {currency}</strong>
                        </td>
                        <td style="padding: 12px; background: #fef3c7; border-radius: 8px; margin: 5px;">
                            <span style="color: #6b7280; font-size: 12px;">الفعلي في الصندوق</span><br>
                            <strong style="color: #d97706; font-size: 18px;">{format_currency(report.get('closingCash', 0))} {currency}</strong>
                        </td>
                    </tr>
                </table>
                
                <!-- Difference -->
                <div style="margin-top: 15px; padding: 15px; background: {'#dcfce7' if diff >= 0 else '#fee2e2'}; border-radius: 8px; display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: #374151; font-weight: 600;">الفرق</span>
                    <span style="color: {diff_color}; font-size: 20px; font-weight: bold;">{diff_sign}{format_currency(diff)} {currency}</span>
                </div>
            </div>
            
            <!-- Sales Summary -->
            <div style="padding: 20px; background: #f9fafb;">
                <h2 style="color: #1f2937; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px; font-size: 18px;">📈 ملخص المبيعات</h2>
                <div style="display: flex; gap: 15px; margin-top: 15px;">
                    <div style="flex: 1; text-align: center; padding: 15px; background: white; border-radius: 8px; border: 1px solid #e5e7eb;">
                        <span style="font-size: 28px; font-weight: bold; color: #3b82f6;">{report.get('salesCount', 0)}</span><br>
                        <span style="color: #6b7280; font-size: 12px;">عدد المبيعات</span>
                    </div>
                    <div style="flex: 1; text-align: center; padding: 15px; background: white; border-radius: 8px; border: 1px solid #e5e7eb;">
                        <span style="font-size: 28px; font-weight: bold; color: #22c55e;">{format_currency(report.get('totalSales', 0))}</span><br>
                        <span style="color: #6b7280; font-size: 12px;">إجمالي المبيعات</span>
                    </div>
                </div>
                
                <!-- Sales by Type -->
                <table style="width: 100%; margin-top: 15px; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden;">
                    <tr style="background: #f3f4f6;">
                        <th style="padding: 10px; text-align: right; font-size: 12px; color: #6b7280;">طريقة الدفع</th>
                        <th style="padding: 10px; text-align: center; font-size: 12px; color: #6b7280;">العدد</th>
                        <th style="padding: 10px; text-align: left; font-size: 12px; color: #6b7280;">المبلغ</th>
                    </tr>
                    <tr style="border-bottom: 1px solid #e5e7eb;">
                        <td style="padding: 10px;">نقدي</td>
                        <td style="padding: 10px; text-align: center;">{len([s for s in report.get('salesByPaymentType', []) if s.get('type') == 'cash'])}</td>
                        <td style="padding: 10px;">{format_currency(report.get('cashSales', 0))} {currency}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #e5e7eb;">
                        <td style="padding: 10px;">دين</td>
                        <td style="padding: 10px; text-align: center;">{len([s for s in report.get('salesByPaymentType', []) if s.get('type') == 'credit'])}</td>
                        <td style="padding: 10px;">{format_currency(report.get('creditSales', 0))} {currency}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px;">جزئي</td>
                        <td style="padding: 10px; text-align: center;">{len([s for s in report.get('salesByPaymentType', []) if s.get('type') == 'partial'])}</td>
                        <td style="padding: 10px;">{format_currency(report.get('partialSales', 0))} {currency}</td>
                    </tr>
                </table>
            </div>
            
            <!-- Debts -->
            <div style="padding: 20px;">
                <div style="background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px; padding: 15px;">
                    <h3 style="color: #dc2626; margin: 0 0 10px 0; font-size: 16px;">🔒 الديون الجديدة</h3>
                    <span style="font-size: 24px; font-weight: bold; color: #dc2626;">{format_currency(report.get('totalDebts', 0))} {currency}</span>
                </div>
            </div>
            
            <!-- Footer -->
            <div style="background: #1f2937; padding: 20px; text-align: center;">
                <p style="color: #9ca3af; margin: 0; font-size: 12px;">
                    تم إنشاء هذا التقرير تلقائياً من نظام NT POS
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    return html

@api_router.post("/email/send-session-report")
async def send_session_report_email(
    report_email: SessionReportEmail,
    user: dict = Depends(require_tenant)
):
    """Send session closing report via email"""
    if not RESEND_AVAILABLE:
        raise HTTPException(status_code=500, detail="خدمة البريد الإلكتروني غير متوفرة")
    
    api_key = os.environ.get('RESEND_API_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="مفتاح API للبريد غير موجود. يرجى إضافة RESEND_API_KEY في الإعدادات")
    
    sender_email = os.environ.get('SENDER_EMAIL', 'onboarding@resend.dev')
    
    # Generate HTML report
    html_content = generate_session_report_html(report_email.report_data)
    
    params = {
        "from": sender_email,
        "to": [report_email.recipient_email],
        "subject": f"تقرير غلق الحصة - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "html": html_content
    }
    
    try:
        email = await asyncio.to_thread(resend.Emails.send, params)
        
        # Log the email
        await db.email_logs.insert_one({
            "id": str(uuid.uuid4()),
            "type": "session_report",
            "recipient": report_email.recipient_email,
            "session_id": report_email.session_id,
            "status": "sent",
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "sent_by": user["id"]
        })
        
        return {
            "success": True,
            "message": f"تم إرسال التقرير إلى {report_email.recipient_email}",
            "email_id": email.get("id")
        }
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"فشل إرسال البريد: {str(e)}")

# ============ EMAIL SETTINGS ============

class EmailSettings(BaseModel):
    enabled: bool = False
    resend_api_key: str = ""
    sender_email: str = "onboarding@resend.dev"
    sender_name: str = "NT POS System"

@api_router.get("/email/settings")
async def get_email_settings(user: dict = Depends(require_tenant)):
    """Get email settings"""
    settings = await db.system_settings.find_one({"type": "email_settings"}, {"_id": 0})
    if not settings:
        return EmailSettings().model_dump()
    
    # Don't expose full API key
    if settings.get("resend_api_key"):
        key = settings["resend_api_key"]
        settings["resend_api_key"] = key[:8] + "..." + key[-4:] if len(key) > 12 else "***configured***"
    
    return settings

@api_router.put("/email/settings")
async def update_email_settings(settings: EmailSettings, user: dict = Depends(require_tenant)):
    """Update email settings"""
    # Check if user is admin
    if user.get("role") not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="غير مصرح لك بتعديل إعدادات البريد")
    
    # Get existing settings to preserve API key if not changed
    existing = await db.system_settings.find_one({"type": "email_settings"})
    
    settings_dict = settings.model_dump()
    
    # If API key looks like masked value, keep the old one
    if settings.resend_api_key and ("..." in settings.resend_api_key or settings.resend_api_key == "***configured***"):
        if existing and existing.get("resend_api_key"):
            settings_dict["resend_api_key"] = existing["resend_api_key"]
    
    # Update in database
    await db.system_settings.update_one(
        {"type": "email_settings"},
        {"$set": {**settings_dict, "type": "email_settings", "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )
    
    # Update environment variable for resend
    if settings_dict.get("resend_api_key") and "..." not in settings_dict["resend_api_key"]:
        os.environ['RESEND_API_KEY'] = settings_dict["resend_api_key"]
        if RESEND_AVAILABLE:
            resend.api_key = settings_dict["resend_api_key"]
    
    if settings_dict.get("sender_email"):
        os.environ['SENDER_EMAIL'] = settings_dict["sender_email"]
    
    return {"success": True, "message": "تم حفظ إعدادات البريد بنجاح"}

@api_router.post("/email/test")
async def test_email_settings(user: dict = Depends(require_tenant)):
    """Send a test email to verify settings"""
    if not RESEND_AVAILABLE:
        raise HTTPException(status_code=500, detail="مكتبة Resend غير متوفرة")
    
    # Get settings from database
    settings = await db.system_settings.find_one({"type": "email_settings"})
    if not settings or not settings.get("resend_api_key"):
        raise HTTPException(status_code=400, detail="يرجى إدخال مفتاح API أولاً")
    
    api_key = settings.get("resend_api_key")
    sender_email = settings.get("sender_email", "onboarding@resend.dev")
    
    # Set API key
    resend.api_key = api_key
    
    # Get user's email
    user_record = await db.users.find_one({"id": user["id"]})
    if not user_record or not user_record.get("email"):
        raise HTTPException(status_code=400, detail="لم يتم العثور على بريدك الإلكتروني")
    
    try:
        params = {
            "from": sender_email,
            "to": [user_record["email"]],
            "subject": "🧪 اختبار إعدادات البريد - NT POS",
            "html": """
            <div dir="rtl" style="font-family: Arial, sans-serif; padding: 20px; background: #f3f4f6;">
                <div style="max-width: 400px; margin: 0 auto; background: white; border-radius: 8px; padding: 30px; text-align: center;">
                    <h2 style="color: #22c55e;">✅ إعدادات البريد تعمل بنجاح!</h2>
                    <p style="color: #6b7280;">هذه رسالة اختبار من نظام NT POS</p>
                    <p style="color: #9ca3af; font-size: 12px; margin-top: 20px;">
                        إذا وصلتك هذه الرسالة، فإن إعدادات البريد الإلكتروني تعمل بشكل صحيح.
                    </p>
                </div>
            </div>
            """
        }
        
        result = await asyncio.to_thread(resend.Emails.send, params)
        return {"success": True, "message": f"تم إرسال بريد اختباري إلى {user_record['email']}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"فشل إرسال البريد: {str(e)}")

# ============ SMART REPORTS ============

class SmartReportSettings(BaseModel):
    daily_report_enabled: bool = False
    daily_report_time: str = "08:00"
    daily_report_recipients: str = ""
    include_ai_tips: bool = True
    include_sales_summary: bool = True
    include_low_stock_alerts: bool = True
    include_debt_reminders: bool = True

@api_router.get("/smart-reports/settings")
async def get_smart_report_settings(user: dict = Depends(require_tenant)):
    """Get smart report settings"""
    settings = await db.system_settings.find_one({"type": "smart_reports"}, {"_id": 0})
    if not settings:
        return SmartReportSettings().model_dump()
    return settings

@api_router.put("/smart-reports/settings")
async def update_smart_report_settings(settings: SmartReportSettings, user: dict = Depends(require_tenant)):
    """Update smart report settings"""
    if user.get("role") not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="غير مصرح")
    
    await db.system_settings.update_one(
        {"type": "smart_reports"},
        {"$set": {**settings.model_dump(), "type": "smart_reports", "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )
    return {"success": True}

@api_router.get("/smart-reports/last")
async def get_last_smart_report(user: dict = Depends(require_tenant)):
    """Get last sent report info"""
    report = await db.smart_reports_log.find_one({}, {"_id": 0}, sort=[("sent_at", -1)])
    return report

@api_router.get("/smart-reports/preview")
async def preview_smart_report(user: dict = Depends(require_tenant)):
    """Generate a preview of the smart report"""
    today = datetime.now(timezone.utc).date()
    yesterday = today - timedelta(days=1)
    
    # Sales summary
    today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
    yesterday_start = datetime.combine(yesterday, datetime.min.time()).replace(tzinfo=timezone.utc)
    
    today_sales = await db.sales.find({"created_at": {"$gte": today_start.isoformat()}}).to_list(1000)
    yesterday_sales = await db.sales.find({
        "created_at": {"$gte": yesterday_start.isoformat(), "$lt": today_start.isoformat()}
    }).to_list(1000)
    
    today_total = sum(s.get("total", 0) for s in today_sales)
    yesterday_total = sum(s.get("total", 0) for s in yesterday_sales)
    today_profit = sum(s.get("profit", 0) for s in today_sales)
    
    change = 0
    if yesterday_total > 0:
        change = ((today_total - yesterday_total) / yesterday_total) * 100
    
    # Low stock products
    low_stock = await db.products.find(
        {"$expr": {"$lt": ["$quantity", {"$ifNull": ["$low_stock_threshold", 10]}]}},
        {"_id": 0, "name_ar": 1, "name_en": 1, "quantity": 1}
    ).to_list(20)
    
    low_stock_list = [{"name": p.get("name_ar") or p.get("name_en"), "quantity": p.get("quantity", 0)} for p in low_stock]
    
    # AI Tips (simple rules-based for now)
    tips = []
    if len(low_stock) > 5:
        tips.append("لديك العديد من المنتجات منخفضة المخزون. يُنصح بمراجعة قائمة المشتريات.")
    if today_total > yesterday_total:
        tips.append(f"مبيعات اليوم أفضل من الأمس بنسبة {change:.1f}%. استمر في العمل الجيد!")
    if today_total < yesterday_total and yesterday_total > 0:
        tips.append("مبيعات اليوم أقل من الأمس. جرب تقديم عروض خاصة لتنشيط المبيعات.")
    if len(today_sales) > 0:
        avg_sale = today_total / len(today_sales)
        tips.append(f"متوسط قيمة الفاتورة اليوم: {avg_sale:.2f} دج")
    
    return {
        "sales": {
            "today_total": today_total,
            "today_count": len(today_sales),
            "today_profit": today_profit,
            "change": change
        },
        "low_stock": low_stock_list,
        "ai_tips": " | ".join(tips) if tips else "لا توجد نصائح حالياً. استمر في العمل!"
    }

@api_router.post("/smart-reports/send-now")
async def send_smart_report_now(user: dict = Depends(require_tenant)):
    """Send smart report immediately"""
    if not RESEND_AVAILABLE:
        raise HTTPException(status_code=500, detail="مكتبة Resend غير متوفرة")
    
    # Get email settings
    email_settings = await db.system_settings.find_one({"type": "email_settings"})
    if not email_settings or not email_settings.get("enabled"):
        raise HTTPException(status_code=400, detail="البريد غير مفعل")
    
    # Get report settings
    report_settings = await db.system_settings.find_one({"type": "smart_reports"})
    recipients = report_settings.get("daily_report_recipients", "") if report_settings else ""
    
    if not recipients:
        # Use current user email
        user_record = await db.users.find_one({"id": user["id"]})
        recipients = user_record.get("email", "") if user_record else ""
    
    if not recipients:
        raise HTTPException(status_code=400, detail="لا يوجد مستلمين محددين")
    
    # Generate report
    preview = await preview_smart_report(user)
    
    # Build HTML email
    html_content = f"""
    <div dir="rtl" style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h1 style="color: #3b82f6;">📊 التقرير اليومي الذكي</h1>
        <p style="color: #666;">{datetime.now().strftime('%Y-%m-%d')}</p>
        
        <div style="background: #f0fdf4; padding: 15px; border-radius: 8px; margin: 15px 0;">
            <h3 style="color: #166534; margin: 0 0 10px 0;">💰 ملخص المبيعات</h3>
            <p>إجمالي اليوم: <strong>{preview['sales']['today_total']:.2f} دج</strong></p>
            <p>عدد المبيعات: <strong>{preview['sales']['today_count']}</strong></p>
            <p>الربح: <strong>{preview['sales']['today_profit']:.2f} دج</strong></p>
            <p>مقارنة بالأمس: <strong style="color: {'#166534' if preview['sales']['change'] >= 0 else '#dc2626'}">{'+' if preview['sales']['change'] >= 0 else ''}{preview['sales']['change']:.1f}%</strong></p>
        </div>
        
        {'<div style="background: #fef3c7; padding: 15px; border-radius: 8px; margin: 15px 0;"><h3 style="color: #92400e; margin: 0 0 10px 0;">⚠️ تنبيهات المخزون ({} منتجات)</h3></div>'.format(len(preview['low_stock'])) if preview['low_stock'] else ''}
        
        <div style="background: #f3e8ff; padding: 15px; border-radius: 8px; margin: 15px 0;">
            <h3 style="color: #7e22ce; margin: 0 0 10px 0;">✨ نصائح ذكية</h3>
            <p>{preview['ai_tips']}</p>
        </div>
        
        <p style="color: #999; font-size: 12px; margin-top: 30px;">
            هذا التقرير تم إنشاؤه تلقائياً من نظام NT POS
        </p>
    </div>
    """
    
    resend.api_key = email_settings.get("resend_api_key")
    
    try:
        params = {
            "from": email_settings.get("sender_email", "onboarding@resend.dev"),
            "to": [r.strip() for r in recipients.split(",")],
            "subject": f"📊 التقرير اليومي الذكي - {datetime.now().strftime('%Y-%m-%d')}",
            "html": html_content
        }
        
        await asyncio.to_thread(resend.Emails.send, params)
        
        # Log the report
        await db.smart_reports_log.insert_one({
            "id": str(uuid.uuid4()),
            "status": "sent",
            "recipients": recipients,
            "sent_at": datetime.now(timezone.utc).isoformat()
        })
        
        return {"success": True, "message": "تم إرسال التقرير بنجاح"}
    except Exception as e:
        await db.smart_reports_log.insert_one({
            "id": str(uuid.uuid4()),
            "status": "failed",
            "recipients": recipients,
            "error": str(e),
            "sent_at": datetime.now(timezone.utc).isoformat()
        })
        raise HTTPException(status_code=500, detail=f"فشل إرسال التقرير: {str(e)}")


# ============ SAAS ROUTES MOVED TO routes/saas_routes.py ============
# All SaaS admin routes (plans, tenants, agents, registration) have been
# refactored to /app/backend/routes/saas_routes.py for better organization.
# Total: 39 endpoints moved

# ============ HEALTH CHECK ============

@api_router.get("/")
async def root():
    return {"message": "NT API is running"}

@api_router.get("/health")
async def health():
    return {"status": "healthy"}

# ============ FEATURES MANAGEMENT ============

@api_router.get("/settings/features")
async def get_features_settings(admin: dict = Depends(get_tenant_admin)):
    """Get enabled/disabled features for the system"""
    settings = await db.settings.find_one({"key": "features"}, {"_id": 0})
    if settings:
        return settings.get("value", {})
    
    # Return default features
    return {
        "sales": {"enabled": True, "subFeatures": {"pos": True, "invoices": True, "quotes": True, "returns": True, "discounts": True, "price_types": True}},
        "inventory": {"enabled": True, "subFeatures": {"products": True, "categories": True, "stock_alerts": True, "barcode": True, "warehouses": False, "stock_transfer": False, "inventory_count": True}},
        "purchases": {"enabled": True, "subFeatures": {"purchase_orders": True, "suppliers": True, "supplier_payments": True, "purchase_returns": False}},
        "customers": {"enabled": True, "subFeatures": {"customer_list": True, "customer_debts": True, "customer_families": True, "blacklist": True, "debt_reminders": True}},
        "employees": {"enabled": True, "subFeatures": {"employee_list": True, "attendance": True, "salaries": True, "commissions": True, "advances": True, "employee_accounts": True}},
        "reports": {"enabled": True, "subFeatures": {"sales_reports": True, "inventory_reports": True, "financial_reports": True, "customer_reports": True, "smart_reports": False, "export_reports": True}},
        "expenses": {"enabled": True, "subFeatures": {"expense_tracking": True, "expense_categories": True, "recurring_expenses": False}},
        "repairs": {"enabled": True, "subFeatures": {"repair_tickets": True, "repair_status": True, "repair_invoice": True}},
        "delivery": {"enabled": True, "subFeatures": {"delivery_tracking": True, "shipping_companies": True, "delivery_fees": True, "yalidine_integration": False}},
        "ecommerce": {"enabled": False, "subFeatures": {"woocommerce": False, "product_sync": False, "order_sync": False}},
        "loyalty": {"enabled": False, "subFeatures": {"loyalty_points": False, "coupons": False, "promotions": True}},
        "notifications": {"enabled": True, "subFeatures": {"push_notifications": True, "email_notifications": False, "sms_notifications": False, "whatsapp_notifications": False}},
        "services": {"enabled": False, "subFeatures": {"flexy_recharge": False, "bill_payment": False}}
    }

@api_router.post("/settings/features")
async def save_features_settings(features: dict, admin: dict = Depends(get_tenant_admin)):
    """Save features settings - Super Admin only applies to all sub-accounts"""
    if admin.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Only admins can change features")
    
    await db.settings.update_one(
        {"key": "features"},
        {"$set": {"key": "features", "value": features, "updated_by": admin["id"], "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )
    return {"message": "Features saved successfully"}

# ============ USER PERMISSIONS MANAGEMENT ============

@api_router.put("/users/{user_id}/permissions")
async def update_user_permissions(user_id: str, data: dict, admin: dict = Depends(get_tenant_admin)):
    """Update specific user permissions"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Only super_admin can modify super_admin permissions
    if user.get("role") == "super_admin" and admin.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Only super admin can modify super admin permissions")
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"permissions": data.get("permissions", {}), "permissions_updated_at": datetime.now(timezone.utc).isoformat(), "permissions_updated_by": admin["id"]}}
    )
    
    return {"message": "Permissions updated successfully"}

@api_router.post("/sales/{sale_id}/log-action")
async def log_sale_action(
    sale_id: str,
    action: str,
    details: dict = {},
    user: dict = Depends(require_tenant)
):
    """Log an action on a sale"""
    log = {
        "id": str(uuid.uuid4()),
        "sale_id": sale_id,
        "action": action,
        "details": details,
        "user_id": user["id"],
        "user_name": user.get("name", user.get("email", "")),
        "user_role": user.get("role", ""),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.sale_audit_logs.insert_one(log)
    return {"message": "Action logged", "log_id": log["id"]}

@api_router.get("/settings/sales-permissions")
async def get_sales_permissions(admin: dict = Depends(get_tenant_admin)):
    """Get sales permission settings"""
    settings = await db.settings.find_one({"key": "sales_permissions"}, {"_id": 0})
    if settings:
        return settings.get("value", {})
    return {
        "allow_employee_edit": False,
        "allow_employee_delete": False,
        "allow_discount_without_approval": True,
        "max_discount_percent": 50.0,
        "max_debt_per_customer": 100000.0,
        "min_sale_price_percent": 80.0
    }

@api_router.post("/settings/sales-permissions")
async def update_sales_permissions(
    settings: dict,
    admin: dict = Depends(get_tenant_admin)
):
    """Update sales permission settings"""
    await db.settings.update_one(
        {"key": "sales_permissions"},
        {"$set": {"key": "sales_permissions", "value": settings}},
        upsert=True
    )
    return {"message": "Settings updated"}

# ============ RECEIPT SETTINGS ============

class ReceiptTemplate(BaseModel):
    id: str = ""
    name: str
    name_ar: str
    width: str = "80mm"  # 58mm, 80mm, A4
    show_logo: bool = True
    show_header: bool = True
    show_footer: bool = True
    header_text: str = ""
    footer_text: str = ""
    font_size: str = "normal"  # small, normal, large
    is_default: bool = False

class ReceiptSettings(BaseModel):
    auto_print: bool = False
    show_print_dialog: bool = True
    default_template_id: str = ""
    templates: List[dict] = []

@api_router.get("/settings/receipt")
async def get_receipt_settings(user: dict = Depends(require_tenant)):
    """Get receipt/invoice settings"""
    settings = await db.settings.find_one({"key": "receipt_settings"}, {"_id": 0})
    if settings:
        return settings.get("value", {})
    # Default settings
    return {
        "auto_print": False,
        "show_print_dialog": True,
        "default_template_id": "default_80mm",
        "templates": [
            {
                "id": "default_58mm",
                "name": "Thermal 58mm",
                "name_ar": "حراري 58 مم",
                "width": "58mm",
                "show_logo": False,
                "show_header": True,
                "show_footer": True,
                "header_text": "",
                "footer_text": "شكراً لزيارتكم",
                "font_size": "small",
                "is_default": False
            },
            {
                "id": "default_80mm",
                "name": "Thermal 80mm",
                "name_ar": "حراري 80 مم",
                "width": "80mm",
                "show_logo": True,
                "show_header": True,
                "show_footer": True,
                "header_text": "",
                "footer_text": "شكراً لزيارتكم",
                "font_size": "normal",
                "is_default": True
            },
            {
                "id": "default_a4",
                "name": "A4 Full Page",
                "name_ar": "صفحة A4 كاملة",
                "width": "A4",
                "show_logo": True,
                "show_header": True,
                "show_footer": True,
                "header_text": "",
                "footer_text": "شكراً لزيارتكم",
                "font_size": "normal",
                "is_default": False
            }
        ]
    }

@api_router.post("/settings/receipt")
async def update_receipt_settings(settings: dict, admin: dict = Depends(get_tenant_admin)):
    """Update receipt settings"""
    await db.settings.update_one(
        {"key": "receipt_settings"},
        {"$set": {"key": "receipt_settings", "value": settings}},
        upsert=True
    )
    return {"message": "Settings updated"}

@api_router.get("/sales/product-tracking/{product_id}")
async def get_product_sales_tracking(
    product_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user: dict = Depends(require_tenant)
):
    """Track all sales for a specific product"""
    query = {"status": {"$ne": "returned"}}
    
    if start_date:
        query["created_at"] = {"$gte": start_date}
    if end_date:
        if "created_at" in query:
            query["created_at"]["$lte"] = end_date + "T23:59:59"
        else:
            query["created_at"] = {"$lte": end_date + "T23:59:59"}
    
    all_sales = await db.sales.find(query, {"_id": 0}).to_list(10000)
    
    # Filter sales containing this product
    product_sales = []
    total_quantity = 0
    total_revenue = 0
    total_profit = 0
    
    for sale in all_sales:
        for item in sale.get("items", []):
            if item.get("product_id") == product_id:
                product_sales.append({
                    "sale_id": sale["id"],
                    "date": sale["created_at"],
                    "customer": sale.get("customer_name", "زبون عابر"),
                    "employee": sale.get("employee_name", ""),
                    "quantity": item.get("quantity", 1),
                    "unit_price": item.get("unit_price", 0),
                    "total": item.get("total", 0),
                    "payment_method": sale.get("payment_method", "cash")
                })
                total_quantity += item.get("quantity", 1)
                total_revenue += item.get("total", 0)
                purchase_price = item.get("purchase_price", item.get("unit_price", 0) * 0.7)
                total_profit += (item.get("unit_price", 0) - purchase_price) * item.get("quantity", 1)
    
    # Get product info
    product = await db.products.find_one({"id": product_id}, {"_id": 0})
    
    return {
        "product": product,
        "sales": product_sales,
        "statistics": {
            "total_sales": len(product_sales),
            "total_quantity": total_quantity,
            "total_revenue": total_revenue,
            "total_profit": total_profit,
            "average_price": total_revenue / total_quantity if total_quantity > 0 else 0
        }
    }


# ============ SYSTEM UPDATES (Super Admin Only) ============

class AnnouncementCreate(BaseModel):
    title_ar: str
    title_fr: str = ""
    message_ar: str
    message_fr: str = ""
    type: str = "info"  # info, feature, maintenance, warning, promotion
    priority: str = "normal"  # low, normal, high, urgent
    target: str = "all"  # all, active

class SettingsPush(BaseModel):
    settings: List[str]

@api_router.get("/system-updates/stats")
async def get_system_stats(admin: dict = Depends(get_super_admin)):
    """Get system statistics for super admin"""
    total_tenants = await db.saas_tenants.count_documents({})
    active_tenants = await db.saas_tenants.count_documents({"status": "active"})
    total_announcements = await db.system_announcements.count_documents({})
    
    return {
        "total_tenants": total_tenants,
        "active_tenants": active_tenants,
        "total_announcements": total_announcements
    }

@api_router.get("/system-updates/announcements")
async def get_announcements(admin: dict = Depends(get_super_admin)):
    """Get all system announcements"""
    announcements = await db.system_announcements.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return announcements

@api_router.post("/system-updates/announcements")
async def create_announcement(data: AnnouncementCreate, admin: dict = Depends(get_super_admin)):
    """Create and broadcast a new announcement"""
    now = datetime.now(timezone.utc).isoformat()
    announcement_id = str(uuid.uuid4())
    
    announcement = {
        "id": announcement_id,
        "title_ar": data.title_ar,
        "title_fr": data.title_fr,
        "message_ar": data.message_ar,
        "message_fr": data.message_fr,
        "type": data.type,
        "priority": data.priority,
        "target": data.target,
        "created_by": admin["id"],
        "created_at": now,
        "read_count": 0
    }
    
    await db.system_announcements.insert_one(announcement)
    
    # Create notifications for all users
    query = {}
    if data.target == "active":
        # Get active tenant IDs
        active_tenants = await db.saas_tenants.find({"status": "active"}, {"id": 1}).to_list(1000)
        tenant_ids = [t["id"] for t in active_tenants]
        query = {"tenant_id": {"$in": tenant_ids}}
    
    users = await db.users.find(query, {"id": 1}).to_list(10000)
    
    notifications = []
    for user in users:
        notifications.append({
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "type": f"system_{data.type}",
            "title": data.title_ar,
            "title_ar": data.title_ar,
            "title_fr": data.title_fr,
            "message": data.message_ar,
            "message_ar": data.message_ar,
            "message_fr": data.message_fr,
            "priority": data.priority,
            "announcement_id": announcement_id,
            "read": False,
            "created_at": now
        })
    
    if notifications:
        await db.notifications.insert_many(notifications)
    
    return {"message": "Announcement created and sent", "id": announcement_id, "recipients": len(notifications)}

@api_router.delete("/system-updates/announcements/{announcement_id}")
async def delete_announcement(announcement_id: str, admin: dict = Depends(get_super_admin)):
    """Delete an announcement"""
    result = await db.system_announcements.delete_one({"id": announcement_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")
    
    # Also delete related notifications
    await db.notifications.delete_many({"announcement_id": announcement_id})
    
    return {"message": "Announcement deleted"}

@api_router.post("/system-updates/push-settings")
async def push_settings(data: SettingsPush, admin: dict = Depends(get_super_admin)):
    """Push settings to all tenants"""
    now = datetime.now(timezone.utc).isoformat()
    
    # Get current admin settings as template
    admin_settings = {}
    
    for setting_type in data.settings:
        if setting_type == "receipt_settings":
            settings = await db.settings.find_one({"type": "receipt"}, {"_id": 0})
            if settings:
                admin_settings["receipt"] = settings
        elif setting_type == "notification_settings":
            settings = await db.notification_settings.find_one({}, {"_id": 0})
            if settings:
                admin_settings["notifications"] = settings
        elif setting_type == "loyalty_settings":
            settings = await db.loyalty_settings.find_one({}, {"_id": 0})
            if settings:
                admin_settings["loyalty"] = settings
        elif setting_type == "pos_settings":
            settings = await db.settings.find_one({"type": "pos"}, {"_id": 0})
            if settings:
                admin_settings["pos"] = settings
    
    # Get all active tenants
    tenants = await db.saas_tenants.find({"status": "active"}, {"database_name": 1}).to_list(1000)
    
    updated_count = 0
    for tenant in tenants:
        try:
            tenant_db = client[tenant["database_name"]]
            for key, value in admin_settings.items():
                if key == "receipt":
                    await tenant_db.settings.update_one(
                        {"type": "receipt"}, 
                        {"$set": value}, 
                        upsert=True
                    )
                elif key == "notifications":
                    await tenant_db.notification_settings.update_one(
                        {}, 
                        {"$set": value}, 
                        upsert=True
                    )
                elif key == "loyalty":
                    await tenant_db.loyalty_settings.update_one(
                        {}, 
                        {"$set": value}, 
                        upsert=True
                    )
                elif key == "pos":
                    await tenant_db.settings.update_one(
                        {"type": "pos"}, 
                        {"$set": value}, 
                        upsert=True
                    )
            updated_count += 1
        except Exception as e:
            print(f"Error updating tenant {tenant.get('database_name')}: {e}")
    
    # Log the action
    await db.system_logs.insert_one({
        "id": str(uuid.uuid4()),
        "action": "push_settings",
        "settings": data.settings,
        "updated_tenants": updated_count,
        "admin_id": admin["id"],
        "created_at": now
    })
    
    return {"message": f"Settings pushed to {updated_count} tenants", "updated_count": updated_count}

# ============ REAL-TIME SYNC SYSTEM ============

class SyncConfigCreate(BaseModel):
    name: str
    sync_types: List[str]  # receipt, notifications, loyalty, pos, products, families, theme
    target: str = "all"  # all, active, selected
    selected_tenants: List[str] = []
    auto_sync: bool = False
    locked: bool = False  # If true, tenants cannot modify

class SyncAction(BaseModel):
    sync_types: List[str]
    target: str = "all"
    selected_tenants: List[str] = []

@api_router.get("/sync/configs")
async def get_sync_configs(admin: dict = Depends(get_super_admin)):
    """Get all sync configurations"""
    configs = await db.sync_configs.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return configs

@api_router.post("/sync/configs")
async def create_sync_config(data: SyncConfigCreate, admin: dict = Depends(get_super_admin)):
    """Create a new sync configuration"""
    now = datetime.now(timezone.utc).isoformat()
    config = {
        "id": str(uuid.uuid4()),
        "name": data.name,
        "sync_types": data.sync_types,
        "target": data.target,
        "selected_tenants": data.selected_tenants,
        "auto_sync": data.auto_sync,
        "locked": data.locked,
        "created_by": admin["id"],
        "created_at": now,
        "last_sync": None
    }
    await db.sync_configs.insert_one(config)
    return config

@api_router.delete("/sync/configs/{config_id}")
async def delete_sync_config(config_id: str, admin: dict = Depends(get_super_admin)):
    """Delete a sync configuration"""
    result = await db.sync_configs.delete_one({"id": config_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Config not found")
    return {"message": "Config deleted"}

@api_router.post("/sync/execute")
async def execute_sync(data: SyncAction, admin: dict = Depends(get_super_admin)):
    """Execute sync to tenants"""
    now = datetime.now(timezone.utc).isoformat()
    sync_id = str(uuid.uuid4())
    
    # Get tenants to sync
    if data.target == "selected" and data.selected_tenants:
        tenants = await db.saas_tenants.find(
            {"id": {"$in": data.selected_tenants}}, 
            {"id": 1, "name": 1, "database_name": 1}
        ).to_list(1000)
    elif data.target == "active":
        tenants = await db.saas_tenants.find(
            {"status": "active"}, 
            {"id": 1, "name": 1, "database_name": 1}
        ).to_list(1000)
    else:
        tenants = await db.saas_tenants.find(
            {}, {"id": 1, "name": 1, "database_name": 1}
        ).to_list(1000)
    
    # Collect data to sync
    sync_data = {}
    sync_labels = {
        "receipt": "إعدادات الإيصال",
        "notifications": "إعدادات الإشعارات",
        "loyalty": "إعدادات الولاء",
        "pos": "إعدادات نقطة البيع",
        "products": "المنتجات",
        "families": "عائلات المنتجات",
        "theme": "تصميم الواجهة"
    }
    
    for sync_type in data.sync_types:
        if sync_type == "receipt":
            settings = await db.settings.find_one({"type": "receipt"}, {"_id": 0})
            if settings: sync_data["receipt"] = settings
        elif sync_type == "notifications":
            settings = await db.notification_settings.find_one({}, {"_id": 0})
            if settings: sync_data["notifications"] = settings
        elif sync_type == "loyalty":
            settings = await db.loyalty_settings.find_one({}, {"_id": 0})
            if settings: sync_data["loyalty"] = settings
        elif sync_type == "pos":
            settings = await db.settings.find_one({"type": "pos"}, {"_id": 0})
            if settings: sync_data["pos"] = settings
        elif sync_type == "products":
            products = await db.products.find({}, {"_id": 0}).to_list(10000)
            sync_data["products"] = products
        elif sync_type == "families":
            families = await db.product_families.find({}, {"_id": 0}).to_list(1000)
            sync_data["families"] = families
        elif sync_type == "theme":
            theme = await db.settings.find_one({"type": "theme"}, {"_id": 0})
            if theme: sync_data["theme"] = theme
    
    # Execute sync
    success_count = 0
    failed_tenants = []
    
    for tenant in tenants:
        try:
            tenant_db = client[tenant["database_name"]]
            
            for key, value in sync_data.items():
                if key == "receipt":
                    await tenant_db.settings.update_one({"type": "receipt"}, {"$set": value}, upsert=True)
                elif key == "notifications":
                    await tenant_db.notification_settings.update_one({}, {"$set": value}, upsert=True)
                elif key == "loyalty":
                    await tenant_db.loyalty_settings.update_one({}, {"$set": value}, upsert=True)
                elif key == "pos":
                    await tenant_db.settings.update_one({"type": "pos"}, {"$set": value}, upsert=True)
                elif key == "products":
                    if value:
                        await tenant_db.products.delete_many({})
                        await tenant_db.products.insert_many(value)
                elif key == "families":
                    if value:
                        await tenant_db.product_families.delete_many({})
                        await tenant_db.product_families.insert_many(value)
                elif key == "theme":
                    await tenant_db.settings.update_one({"type": "theme"}, {"$set": value}, upsert=True)
            
            # Send notification to tenant
            await tenant_db.notifications.insert_one({
                "id": str(uuid.uuid4()),
                "type": "system_update",
                "title": "تحديث من الإدارة",
                "message": f"تم تحديث: {', '.join([sync_labels.get(t, t) for t in data.sync_types])}",
                "priority": "high",
                "read": False,
                "created_at": now
            })
            
            success_count += 1
        except Exception as e:
            failed_tenants.append({"id": tenant["id"], "name": tenant["name"], "error": str(e)})
    
    # Log sync action
    sync_log = {
        "id": sync_id,
        "sync_types": data.sync_types,
        "target": data.target,
        "total_tenants": len(tenants),
        "success_count": success_count,
        "failed_count": len(failed_tenants),
        "failed_tenants": failed_tenants,
        "admin_id": admin["id"],
        "admin_name": admin.get("name", ""),
        "created_at": now
    }
    await db.sync_logs.insert_one(sync_log)
    
    return {
        "message": f"تم المزامنة بنجاح إلى {success_count} مشترك",
        "sync_id": sync_id,
        "success_count": success_count,
        "failed_count": len(failed_tenants),
        "failed_tenants": failed_tenants
    }

@api_router.get("/sync/logs")
async def get_sync_logs(admin: dict = Depends(get_super_admin), limit: int = 50):
    """Get sync history logs"""
    logs = await db.sync_logs.find({}, {"_id": 0}).sort("created_at", -1).to_list(limit)
    return logs

@api_router.get("/sync/available-types")
async def get_available_sync_types(admin: dict = Depends(get_super_admin)):
    """Get available sync types with counts"""
    products_count = await db.products.count_documents({})
    families_count = await db.product_families.count_documents({})
    
    return [
        {"id": "receipt", "name": "إعدادات الإيصال", "name_fr": "Paramètres du reçu", "icon": "Receipt", "count": 1},
        {"id": "notifications", "name": "إعدادات الإشعارات", "name_fr": "Paramètres des notifications", "icon": "Bell", "count": 1},
        {"id": "loyalty", "name": "إعدادات الولاء", "name_fr": "Paramètres de fidélité", "icon": "Award", "count": 1},
        {"id": "pos", "name": "إعدادات نقطة البيع", "name_fr": "Paramètres POS", "icon": "Store", "count": 1},
        {"id": "products", "name": "المنتجات", "name_fr": "Produits", "icon": "Package", "count": products_count},
        {"id": "families", "name": "عائلات المنتجات", "name_fr": "Familles de produits", "icon": "Folder", "count": families_count},
        {"id": "theme", "name": "تصميم الواجهة", "name_fr": "Thème", "icon": "Palette", "count": 1}
    ]

@api_router.post("/sync/lock-settings")
async def lock_tenant_settings(tenant_ids: List[str], lock: bool, admin: dict = Depends(get_super_admin)):
    """Lock or unlock settings for specific tenants"""
    now = datetime.now(timezone.utc).isoformat()
    
    for tenant_id in tenant_ids:
        tenant = await db.saas_tenants.find_one({"id": tenant_id})
        if tenant:
            tenant_db = client[tenant["database_name"]]
            await tenant_db.settings.update_one(
                {"type": "admin_lock"},
                {"$set": {"locked": lock, "updated_at": now}},
                upsert=True
            )
    
    return {"message": f"تم {'قفل' if lock else 'فتح'} الإعدادات لـ {len(tenant_ids)} مشترك"}


# ============ TENANT DATABASE MANAGEMENT ============

@api_router.get("/tenant/database-info")
async def get_tenant_database_info(current_user: dict = Depends(require_tenant)):
    """Get database info for current tenant"""
    tenant_id = current_user.get("tenant_id") or current_user.get("id")
    
    # Get tenant info
    tenant = await db.saas_tenants.find_one({"id": tenant_id}, {"_id": 0})
    
    if tenant:
        db_name = f"tenant_{tenant_id.replace('-', '_')}"
        try:
            tenant_db = client[db_name]
            stats = await tenant_db.command("dbStats")
            cols = await tenant_db.list_collection_names()
            docs = sum([await tenant_db[c].count_documents({}) for c in cols])
            
            return {
                "size_mb": round(stats.get("dataSize", 0) / (1024 * 1024), 2),
                "collections_count": len(cols),
                "documents_count": docs,
                "last_backup": tenant.get("last_backup"),
                "is_frozen": tenant.get("is_frozen", False),
                "status": "frozen" if tenant.get("is_frozen") else "healthy"
            }
        except Exception as e:
            logger.error(f"Error getting tenant DB info: {e}")
    
    # Fallback: return estimated data
    return {
        "size_mb": 0,
        "collections_count": 8,
        "documents_count": 0,
        "last_backup": None,
        "is_frozen": False,
        "status": "healthy"
    }

@api_router.post("/tenant/request-backup")
async def request_tenant_backup(current_user: dict = Depends(require_tenant)):
    """Request backup for tenant database"""
    tenant_id = current_user.get("tenant_id") or current_user.get("id")
    now = datetime.now(timezone.utc).isoformat()
    
    # Create backup request
    request_id = str(uuid.uuid4())
    await db.backup_requests.insert_one({
        "id": request_id,
        "tenant_id": tenant_id,
        "tenant_name": current_user.get("name") or current_user.get("company_name"),
        "status": "pending",
        "requested_at": now,
        "processed_at": None
    })
    
    # Log operation
    await db.database_operation_logs.insert_one({
        "id": str(uuid.uuid4()),
        "operation": "backup_request",
        "database_id": tenant_id,
        "database_name": f"tenant_{tenant_id.replace('-', '_')}",
        "executed_by": current_user.get("name"),
        "status": "pending",
        "details": "طلب نسخة احتياطية من المشترك",
        "created_at": now
    })
    
    return {"message": "تم إرسال طلب النسخ الاحتياطي", "request_id": request_id}

@api_router.get("/tenant/export-data")
async def export_tenant_data(current_user: dict = Depends(require_tenant)):
    """Export tenant's own data"""
    import json
    
    tenant_id = current_user.get("tenant_id") or current_user.get("id")
    
    # Check if frozen
    tenant = await db.saas_tenants.find_one({"id": tenant_id}, {"_id": 0})
    if tenant and tenant.get("is_frozen"):
        raise HTTPException(status_code=403, detail="قاعدة البيانات مجمدة")
    
    db_name = f"tenant_{tenant_id.replace('-', '_')}"
    
    try:
        tenant_db = client[db_name]
        export_data = {}
        
        # Export allowed collections only
        allowed_collections = ["products", "customers", "suppliers", "employees", "sales", "expenses", "settings"]
        
        for col in allowed_collections:
            try:
                docs = await tenant_db[col].find({}, {"_id": 0}).to_list(100000)
                export_data[col] = docs
            except Exception:
                export_data[col] = []
        
        export_data["exported_at"] = datetime.now(timezone.utc).isoformat()
        export_data["tenant_id"] = tenant_id
        
        content = json.dumps(export_data, ensure_ascii=False, indent=2, default=str)
        
        # Log export
        await db.database_operation_logs.insert_one({
            "id": str(uuid.uuid4()),
            "operation": "self_export",
            "database_id": tenant_id,
            "database_name": db_name,
            "executed_by": current_user.get("name"),
            "status": "success",
            "details": "تصدير بيانات ذاتي",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        return StreamingResponse(
            io.BytesIO(content.encode('utf-8')),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={db_name}_export.json"}
        )
    except Exception as e:
        logger.error(f"Error exporting tenant data: {e}")
        raise HTTPException(status_code=500, detail="حدث خطأ أثناء التصدير")



# ============ DATABASE MANAGEMENT MOVED TO routes/saas_routes.py ============

# ============ SENDGRID EMAIL NOTIFICATIONS ============

class SendGridSettings(BaseModel):
    enabled: bool = False
    api_key: str = ""
    sender_email: str = ""
    sender_name: str = "NT Commerce"
    # Notification types
    new_sale_notification: bool = True
    low_stock_notification: bool = True
    daily_report: bool = False
    weekly_report: bool = False
    notification_email: str = ""

class EmailNotificationRequest(BaseModel):
    notification_type: str  # new_sale, low_stock, daily_report, weekly_report, custom
    recipient_email: str
    subject: str = ""
    data: dict = {}

async def send_email_with_sendgrid(to_email: str, subject: str, html_content: str, settings: dict = None):
    """Send email using SendGrid"""
    if not SENDGRID_AVAILABLE:
        raise HTTPException(status_code=500, detail="SendGrid غير متوفر")
    
    # Get settings from database if not provided
    if not settings:
        settings = await main_db.system_settings.find_one({"type": "sendgrid_settings"})
    
    if not settings or not settings.get("api_key"):
        raise HTTPException(status_code=400, detail="يرجى إعداد مفتاح SendGrid أولاً")
    
    try:
        sg = SendGridAPIClient(settings["api_key"])
        from_email = Email(settings.get("sender_email", "noreply@ntcommerce.com"), settings.get("sender_name", "NT Commerce"))
        to_email_obj = To(to_email)
        content = Content("text/html", html_content)
        mail = Mail(from_email, to_email_obj, subject, content)
        
        response = sg.send(mail)
        return response.status_code == 202
    except Exception as e:
        logger.error(f"SendGrid error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"فشل إرسال البريد: {str(e)}")

def generate_sale_notification_html(sale_data: dict):
    """Generate HTML for sale notification"""
    return f"""
    <div dir="rtl" style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #f8f9fa; padding: 20px;">
        <div style="background: white; border-radius: 12px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <div style="text-align: center; margin-bottom: 20px;">
                <h1 style="color: #22c55e; margin: 0;">🛒 عملية بيع جديدة</h1>
            </div>
            <div style="background: #f0fdf4; border-radius: 8px; padding: 15px; margin: 15px 0;">
                <p style="margin: 5px 0;"><strong>رقم الفاتورة:</strong> {sale_data.get('invoice_number', 'N/A')}</p>
                <p style="margin: 5px 0;"><strong>الزبون:</strong> {sale_data.get('customer_name', 'زبون عام')}</p>
                <p style="margin: 5px 0;"><strong>المبلغ الإجمالي:</strong> <span style="color: #16a34a; font-size: 1.2em; font-weight: bold;">{sale_data.get('total', 0):,.2f} دج</span></p>
                <p style="margin: 5px 0;"><strong>طريقة الدفع:</strong> {sale_data.get('payment_method', 'نقداً')}</p>
                <p style="margin: 5px 0;"><strong>عدد المنتجات:</strong> {sale_data.get('items_count', 0)}</p>
            </div>
            <p style="color: #6b7280; font-size: 12px; text-align: center; margin-top: 20px;">
                تم إرسال هذا الإشعار تلقائياً من نظام NT Commerce
            </p>
        </div>
    </div>
    """

def generate_low_stock_notification_html(products: list):
    """Generate HTML for low stock notification"""
    products_html = ""
    for p in products[:20]:  # Limit to 20 products
        products_html += f"""
        <tr>
            <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">{p.get('name', 'N/A')}</td>
            <td style="padding: 8px; border-bottom: 1px solid #e5e7eb; text-align: center; color: {'#dc2626' if p.get('stock', 0) == 0 else '#f59e0b'};">
                {p.get('stock', 0)}
            </td>
            <td style="padding: 8px; border-bottom: 1px solid #e5e7eb; text-align: center;">{p.get('min_quantity', 10)}</td>
        </tr>
        """
    
    return f"""
    <div dir="rtl" style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #f8f9fa; padding: 20px;">
        <div style="background: white; border-radius: 12px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <div style="text-align: center; margin-bottom: 20px;">
                <h1 style="color: #f59e0b; margin: 0;">⚠️ تنبيه انخفاض المخزون</h1>
                <p style="color: #6b7280;">يوجد {len(products)} منتج بحاجة إلى إعادة تزويد</p>
            </div>
            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                <thead>
                    <tr style="background: #f3f4f6;">
                        <th style="padding: 10px; text-align: right;">المنتج</th>
                        <th style="padding: 10px; text-align: center;">الكمية الحالية</th>
                        <th style="padding: 10px; text-align: center;">الحد الأدنى</th>
                    </tr>
                </thead>
                <tbody>
                    {products_html}
                </tbody>
            </table>
            <p style="color: #6b7280; font-size: 12px; text-align: center; margin-top: 20px;">
                تم إرسال هذا الإشعار تلقائياً من نظام NT Commerce
            </p>
        </div>
    </div>
    """

def generate_daily_report_html(report_data: dict):
    """Generate HTML for daily report"""
    return f"""
    <div dir="rtl" style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #f8f9fa; padding: 20px;">
        <div style="background: white; border-radius: 12px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <div style="text-align: center; margin-bottom: 20px;">
                <h1 style="color: #3b82f6; margin: 0;">📊 التقرير اليومي</h1>
                <p style="color: #6b7280;">{report_data.get('date', datetime.now().strftime('%Y-%m-%d'))}</p>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 20px 0;">
                <div style="background: #f0fdf4; border-radius: 8px; padding: 15px; text-align: center;">
                    <p style="margin: 0; color: #6b7280; font-size: 12px;">إجمالي المبيعات</p>
                    <p style="margin: 5px 0; color: #16a34a; font-size: 1.5em; font-weight: bold;">{report_data.get('total_sales', 0):,.2f} دج</p>
                </div>
                <div style="background: #eff6ff; border-radius: 8px; padding: 15px; text-align: center;">
                    <p style="margin: 0; color: #6b7280; font-size: 12px;">عدد الفواتير</p>
                    <p style="margin: 5px 0; color: #3b82f6; font-size: 1.5em; font-weight: bold;">{report_data.get('sales_count', 0)}</p>
                </div>
                <div style="background: #fef3c7; border-radius: 8px; padding: 15px; text-align: center;">
                    <p style="margin: 0; color: #6b7280; font-size: 12px;">صافي الربح</p>
                    <p style="margin: 5px 0; color: #d97706; font-size: 1.5em; font-weight: bold;">{report_data.get('total_profit', 0):,.2f} دج</p>
                </div>
                <div style="background: #fce7f3; border-radius: 8px; padding: 15px; text-align: center;">
                    <p style="margin: 0; color: #6b7280; font-size: 12px;">المصاريف</p>
                    <p style="margin: 5px 0; color: #db2777; font-size: 1.5em; font-weight: bold;">{report_data.get('total_expenses', 0):,.2f} دج</p>
                </div>
            </div>
            
            <div style="background: #f3f4f6; border-radius: 8px; padding: 15px; margin-top: 15px;">
                <p style="margin: 5px 0;"><strong>أفضل منتج مبيعاً:</strong> {report_data.get('top_product', 'N/A')}</p>
                <p style="margin: 5px 0;"><strong>زبائن جدد:</strong> {report_data.get('new_customers', 0)}</p>
                <p style="margin: 5px 0;"><strong>ديون جديدة:</strong> {report_data.get('new_debts', 0):,.2f} دج</p>
                <p style="margin: 5px 0;"><strong>ديون محصلة:</strong> {report_data.get('collected_debts', 0):,.2f} دج</p>
            </div>
            
            <p style="color: #6b7280; font-size: 12px; text-align: center; margin-top: 20px;">
                تم إرسال هذا التقرير تلقائياً من نظام NT Commerce
            </p>
        </div>
    </div>
    """

@api_router.get("/notifications/sendgrid/settings")
async def get_sendgrid_settings(user: dict = Depends(require_tenant)):
    """Get SendGrid email notification settings"""
    settings = await db.system_settings.find_one({"type": "sendgrid_settings"}, {"_id": 0})
    if not settings:
        return SendGridSettings().model_dump()
    
    # Mask API key
    if settings.get("api_key"):
        key = settings["api_key"]
        settings["api_key"] = key[:8] + "..." + key[-4:] if len(key) > 12 else "***configured***"
    
    return settings

@api_router.put("/notifications/sendgrid/settings")
async def update_sendgrid_settings(settings: SendGridSettings, user: dict = Depends(require_tenant)):
    """Update SendGrid email notification settings"""
    if user.get("role") not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="غير مصرح لك")
    
    # Get existing settings to preserve API key if masked
    existing = await db.system_settings.find_one({"type": "sendgrid_settings"})
    
    settings_dict = settings.model_dump()
    
    # If API key looks masked, keep the old one
    if settings.api_key and ("..." in settings.api_key or settings.api_key == "***configured***"):
        if existing and existing.get("api_key"):
            settings_dict["api_key"] = existing["api_key"]
    
    await db.system_settings.update_one(
        {"type": "sendgrid_settings"},
        {"$set": {**settings_dict, "type": "sendgrid_settings", "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )
    
    return {"success": True, "message": "تم حفظ إعدادات الإشعارات"}

@api_router.post("/notifications/sendgrid/test")
async def test_sendgrid_settings(user: dict = Depends(require_tenant)):
    """Send a test email via SendGrid"""
    settings = await db.system_settings.find_one({"type": "sendgrid_settings"})
    if not settings or not settings.get("api_key"):
        raise HTTPException(status_code=400, detail="يرجى إعداد مفتاح SendGrid أولاً")
    
    user_record = await db.users.find_one({"id": user["id"]})
    if not user_record or not user_record.get("email"):
        raise HTTPException(status_code=400, detail="لم يتم العثور على بريدك الإلكتروني")
    
    test_html = """
    <div dir="rtl" style="font-family: Arial, sans-serif; padding: 20px; background: #f3f4f6;">
        <div style="max-width: 400px; margin: 0 auto; background: white; border-radius: 8px; padding: 30px; text-align: center;">
            <h2 style="color: #22c55e;">✅ SendGrid يعمل بنجاح!</h2>
            <p style="color: #6b7280;">هذه رسالة اختبار من نظام NT Commerce</p>
            <p style="color: #9ca3af; font-size: 12px; margin-top: 20px;">
                إذا وصلتك هذه الرسالة، فإن إعدادات البريد الإلكتروني تعمل بشكل صحيح.
            </p>
        </div>
    </div>
    """
    
    try:
        await send_email_with_sendgrid(user_record["email"], "🧪 اختبار SendGrid - NT Commerce", test_html, settings)
        return {"success": True, "message": f"تم إرسال بريد اختباري إلى {user_record['email']}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/notifications/send")
async def send_notification(request: EmailNotificationRequest, user: dict = Depends(require_tenant)):
    """Send a notification email"""
    settings = await db.system_settings.find_one({"type": "sendgrid_settings"})
    if not settings or not settings.get("enabled"):
        raise HTTPException(status_code=400, detail="إشعارات البريد غير مفعلة")
    
    subject = request.subject
    html_content = ""
    
    if request.notification_type == "new_sale":
        subject = subject or f"🛒 عملية بيع جديدة - {request.data.get('invoice_number', '')}"
        html_content = generate_sale_notification_html(request.data)
    elif request.notification_type == "low_stock":
        subject = subject or "⚠️ تنبيه انخفاض المخزون"
        html_content = generate_low_stock_notification_html(request.data.get("products", []))
    elif request.notification_type == "daily_report":
        subject = subject or f"📊 التقرير اليومي - {datetime.now().strftime('%Y-%m-%d')}"
        html_content = generate_daily_report_html(request.data)
    else:
        html_content = request.data.get("html_content", "<p>إشعار من NT Commerce</p>")
    
    try:
        await send_email_with_sendgrid(request.recipient_email, subject, html_content, settings)
        
        # Log the notification
        await db.notification_logs.insert_one({
            "id": str(uuid.uuid4()),
            "type": request.notification_type,
            "recipient": request.recipient_email,
            "subject": subject,
            "status": "sent",
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "sent_by": user["id"]
        })
        
        return {"success": True, "message": "تم إرسال الإشعار بنجاح"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/notifications/check-low-stock")
async def check_and_notify_low_stock(user: dict = Depends(require_tenant)):
    """Check for low stock products and send notification"""
    settings = await db.system_settings.find_one({"type": "sendgrid_settings"})
    if not settings or not settings.get("enabled") or not settings.get("low_stock_notification"):
        return {"success": False, "message": "إشعارات انخفاض المخزون غير مفعلة"}
    
    # Get low stock products
    low_stock_products = await db.products.find({
        "$expr": {"$lte": ["$stock", "$min_quantity"]}
    }).to_list(100)
    
    if not low_stock_products:
        return {"success": True, "message": "لا توجد منتجات منخفضة المخزون"}
    
    products_list = [{"name": p.get("name", ""), "stock": p.get("stock", 0), "min_quantity": p.get("min_quantity", 10)} for p in low_stock_products]
    
    recipient = settings.get("notification_email")
    if not recipient:
        return {"success": False, "message": "يرجى إعداد بريد الإشعارات"}
    
    html_content = generate_low_stock_notification_html(products_list)
    
    try:
        await send_email_with_sendgrid(recipient, "⚠️ تنبيه انخفاض المخزون - NT Commerce", html_content, settings)
        return {"success": True, "message": f"تم إرسال تنبيه بـ {len(products_list)} منتج منخفض المخزون"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/notifications/send-daily-report")
async def send_daily_report(user: dict = Depends(require_tenant)):
    """Generate and send daily report"""
    settings = await db.system_settings.find_one({"type": "sendgrid_settings"})
    if not settings or not settings.get("enabled"):
        raise HTTPException(status_code=400, detail="إشعارات البريد غير مفعلة")
    
    recipient = settings.get("notification_email")
    if not recipient:
        raise HTTPException(status_code=400, detail="يرجى إعداد بريد الإشعارات")
    
    # Generate report data
    today = datetime.now(timezone.utc).date()
    today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
    
    sales = await db.sales.find({"created_at": {"$gte": today_start.isoformat()}}).to_list(1000)
    expenses = await db.expenses.find({"created_at": {"$gte": today_start.isoformat()}}).to_list(1000)
    
    total_sales = sum(s.get("total", 0) for s in sales)
    total_profit = sum(s.get("profit", 0) for s in sales)
    total_expenses = sum(e.get("amount", 0) for e in expenses)
    
    # Find top product
    product_sales = {}
    for s in sales:
        for item in s.get("items", []):
            pid = item.get("product_id", "")
            product_sales[pid] = product_sales.get(pid, 0) + item.get("quantity", 0)
    
    top_product_id = max(product_sales, key=product_sales.get) if product_sales else None
    top_product = await db.products.find_one({"id": top_product_id}) if top_product_id else None
    
    report_data = {
        "date": today.strftime('%Y-%m-%d'),
        "total_sales": total_sales,
        "sales_count": len(sales),
        "total_profit": total_profit,
        "total_expenses": total_expenses,
        "top_product": top_product.get("name", "N/A") if top_product else "N/A",
        "new_customers": await db.customers.count_documents({"created_at": {"$gte": today_start.isoformat()}}),
        "new_debts": sum(s.get("remaining", 0) for s in sales if s.get("payment_status") == "partial"),
        "collected_debts": 0  # Would need debt payments tracking
    }
    
    html_content = generate_daily_report_html(report_data)
    
    try:
        await send_email_with_sendgrid(recipient, f"📊 التقرير اليومي - {today.strftime('%Y-%m-%d')}", html_content, settings)
        return {"success": True, "message": "تم إرسال التقرير اليومي"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ STRIPE PAYMENT INTEGRATION ============

# Subscription packages (prices defined on backend for security)
SUBSCRIPTION_PACKAGES = {
    "basic_monthly": {"name": "الباقة الأساسية - شهري", "amount": 2500.0, "duration_days": 30, "currency": "dzd"},
    "basic_yearly": {"name": "الباقة الأساسية - سنوي", "amount": 25000.0, "duration_days": 365, "currency": "dzd"},
    "pro_monthly": {"name": "الباقة المتقدمة - شهري", "amount": 5000.0, "duration_days": 30, "currency": "dzd"},
    "pro_yearly": {"name": "الباقة المتقدمة - سنوي", "amount": 50000.0, "duration_days": 365, "currency": "dzd"},
    "enterprise_monthly": {"name": "باقة المؤسسات - شهري", "amount": 10000.0, "duration_days": 30, "currency": "dzd"},
    "enterprise_yearly": {"name": "باقة المؤسسات - سنوي", "amount": 100000.0, "duration_days": 365, "currency": "dzd"},
}

class CreateCheckoutRequest(BaseModel):
    package_id: str
    origin_url: str

class PaymentRecord(BaseModel):
    tenant_id: Optional[str] = None
    amount: float
    currency: str = "dzd"
    payment_method: str = "stripe"
    description: str = ""
    invoice_number: str = ""
    status: str = "pending"
    metadata: dict = {}

class PaymentUpdateRequest(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    invoice_number: Optional[str] = None

@api_router.get("/payments/packages")
async def get_subscription_packages():
    """Get available subscription packages"""
    packages = []
    for pkg_id, pkg in SUBSCRIPTION_PACKAGES.items():
        packages.append({
            "id": pkg_id,
            "name": pkg["name"],
            "amount": pkg["amount"],
            "duration_days": pkg["duration_days"],
            "currency": pkg["currency"]
        })
    return packages

@api_router.post("/payments/create-checkout")
async def create_checkout_session(request: CreateCheckoutRequest, http_request: Request):
    """Create a Stripe checkout session"""
    if not STRIPE_AVAILABLE:
        raise HTTPException(status_code=500, detail="Stripe غير متوفر")
    
    package = SUBSCRIPTION_PACKAGES.get(request.package_id)
    if not package:
        raise HTTPException(status_code=400, detail="الباقة غير موجودة")
    
    api_key = os.environ.get("STRIPE_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="مفتاح Stripe غير موجود")
    
    try:
        # Build URLs from origin
        success_url = f"{request.origin_url}/payment-success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{request.origin_url}/payment-cancel"
        
        # Create webhook URL
        host_url = str(http_request.base_url)
        webhook_url = f"{host_url}api/webhook/stripe"
        
        stripe_checkout = StripeCheckout(api_key=api_key, webhook_url=webhook_url)
        
        checkout_request = CheckoutSessionRequest(
            amount=package["amount"],
            currency="usd",  # Stripe requires USD for most operations
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "package_id": request.package_id,
                "package_name": package["name"],
                "duration_days": str(package["duration_days"]),
                "source": "nt_commerce"
            }
        )
        
        session: CheckoutSessionResponse = await stripe_checkout.create_checkout_session(checkout_request)
        
        # Create payment transaction record
        transaction_id = str(uuid.uuid4())
        await main_db.payment_transactions.insert_one({
            "id": transaction_id,
            "session_id": session.session_id,
            "package_id": request.package_id,
            "package_name": package["name"],
            "amount": package["amount"],
            "currency": package["currency"],
            "payment_status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "metadata": {
                "package_id": request.package_id,
                "duration_days": package["duration_days"]
            }
        })
        
        return {
            "url": session.url,
            "session_id": session.session_id,
            "transaction_id": transaction_id
        }
    except Exception as e:
        logger.error(f"Stripe checkout error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"فشل إنشاء جلسة الدفع: {str(e)}")

@api_router.get("/payments/status/{session_id}")
async def get_payment_status(session_id: str, http_request: Request):
    """Get payment status from Stripe"""
    if not STRIPE_AVAILABLE:
        raise HTTPException(status_code=500, detail="Stripe غير متوفر")
    
    api_key = os.environ.get("STRIPE_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="مفتاح Stripe غير موجود")
    
    try:
        host_url = str(http_request.base_url)
        webhook_url = f"{host_url}api/webhook/stripe"
        stripe_checkout = StripeCheckout(api_key=api_key, webhook_url=webhook_url)
        
        status: CheckoutStatusResponse = await stripe_checkout.get_checkout_status(session_id)
        
        # Update transaction in database
        await main_db.payment_transactions.update_one(
            {"session_id": session_id},
            {"$set": {
                "payment_status": status.payment_status,
                "status": status.status,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        return {
            "status": status.status,
            "payment_status": status.payment_status,
            "amount_total": status.amount_total,
            "currency": status.currency,
            "metadata": status.metadata
        }
    except Exception as e:
        logger.error(f"Stripe status error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"فشل التحقق من حالة الدفع: {str(e)}")

@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks"""
    if not STRIPE_AVAILABLE:
        raise HTTPException(status_code=500, detail="Stripe غير متوفر")
    
    api_key = os.environ.get("STRIPE_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="مفتاح Stripe غير موجود")
    
    try:
        body = await request.body()
        signature = request.headers.get("Stripe-Signature")
        
        host_url = str(request.base_url)
        webhook_url = f"{host_url}api/webhook/stripe"
        stripe_checkout = StripeCheckout(api_key=api_key, webhook_url=webhook_url)
        
        webhook_response = await stripe_checkout.handle_webhook(body, signature)
        
        # Update payment transaction
        if webhook_response.session_id:
            await main_db.payment_transactions.update_one(
                {"session_id": webhook_response.session_id},
                {"$set": {
                    "payment_status": webhook_response.payment_status,
                    "event_type": webhook_response.event_type,
                    "event_id": webhook_response.event_id,
                    "webhook_received_at": datetime.now(timezone.utc).isoformat()
                }}
            )
        
        return {"received": True}
    except Exception as e:
        logger.error(f"Stripe webhook error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# Payment Records Management (for manual/offline payments)
@api_router.get("/payments/records")
async def get_payment_records(
    page: int = 1,
    limit: int = 20,
    status: Optional[str] = None,
    admin: dict = Depends(get_super_admin)
):
    """Get all payment records"""
    query = {}
    if status:
        query["payment_status"] = status
    
    skip = (page - 1) * limit
    records = await main_db.payment_transactions.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    total = await main_db.payment_transactions.count_documents(query)
    
    return {
        "records": records,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit
    }

@api_router.post("/payments/records")
async def create_payment_record(payment: PaymentRecord, admin: dict = Depends(get_super_admin)):
    """Create a manual payment record"""
    record_id = str(uuid.uuid4())
    record = {
        "id": record_id,
        "tenant_id": payment.tenant_id,
        "amount": payment.amount,
        "currency": payment.currency,
        "payment_method": payment.payment_method,
        "description": payment.description,
        "invoice_number": payment.invoice_number or f"INV-{datetime.now().strftime('%Y%m%d')}-{record_id[:8].upper()}",
        "payment_status": payment.status,
        "metadata": payment.metadata,
        "created_by": admin.get("id"),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await main_db.payment_transactions.insert_one(record)
    
    # If payment is for a tenant, update subscription if paid
    if payment.tenant_id and payment.status == "paid":
        # Extend subscription
        tenant = await main_db.saas_tenants.find_one({"id": payment.tenant_id})
        if tenant:
            current_end = tenant.get("subscription_end")
            if current_end:
                try:
                    end_date = datetime.fromisoformat(current_end.replace('Z', '+00:00'))
                except Exception:
                    end_date = datetime.now(timezone.utc)
            else:
                end_date = datetime.now(timezone.utc)
            
            # Default 30 days extension for manual payments
            new_end = end_date + timedelta(days=30)
            await main_db.saas_tenants.update_one(
                {"id": payment.tenant_id},
                {"$set": {"subscription_end": new_end.isoformat()}}
            )
    
    return {"id": record_id, "message": "تم إنشاء سجل الدفع"}

@api_router.put("/payments/records/{record_id}")
async def update_payment_record(record_id: str, update: PaymentUpdateRequest, admin: dict = Depends(get_super_admin)):
    """Update a payment record"""
    update_data = {}
    if update.status:
        update_data["payment_status"] = update.status
    if update.notes:
        update_data["notes"] = update.notes
    if update.invoice_number:
        update_data["invoice_number"] = update.invoice_number
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    update_data["updated_by"] = admin.get("id")
    
    result = await main_db.payment_transactions.update_one(
        {"id": record_id},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="سجل الدفع غير موجود")
    
    return {"success": True, "message": "تم تحديث سجل الدفع"}

@api_router.delete("/payments/records/{record_id}")
async def delete_payment_record(record_id: str, admin: dict = Depends(get_super_admin)):
    """Delete a payment record"""
    result = await main_db.payment_transactions.delete_one({"id": record_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="سجل الدفع غير موجود")
    
    return {"success": True, "message": "تم حذف سجل الدفع"}

# Invoice Generation
@api_router.get("/payments/invoice/{record_id}")
async def generate_invoice(record_id: str, admin: dict = Depends(get_super_admin)):
    """Generate invoice for a payment"""
    record = await main_db.payment_transactions.find_one({"id": record_id}, {"_id": 0})
    if not record:
        raise HTTPException(status_code=404, detail="سجل الدفع غير موجود")
    
    # Get tenant info if available
    tenant = None
    if record.get("tenant_id"):
        tenant = await main_db.saas_tenants.find_one({"id": record["tenant_id"]}, {"_id": 0})
    
    invoice_html = f"""
    <html dir="rtl">
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 40px; }}
            .header {{ text-align: center; border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 30px; }}
            .invoice-info {{ display: flex; justify-content: space-between; margin-bottom: 30px; }}
            .table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            .table th, .table td {{ border: 1px solid #ddd; padding: 12px; text-align: right; }}
            .table th {{ background: #f3f4f6; }}
            .total {{ font-size: 1.2em; font-weight: bold; text-align: left; margin-top: 20px; }}
            .footer {{ text-align: center; margin-top: 50px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>فاتورة</h1>
            <p>NT Commerce</p>
        </div>
        
        <div class="invoice-info">
            <div>
                <p><strong>رقم الفاتورة:</strong> {record.get('invoice_number', 'N/A')}</p>
                <p><strong>التاريخ:</strong> {record.get('created_at', '')[:10]}</p>
                <p><strong>الحالة:</strong> {'مدفوع' if record.get('payment_status') == 'paid' else 'قيد الانتظار'}</p>
            </div>
            <div>
                <p><strong>العميل:</strong> {tenant.get('business_name', 'N/A') if tenant else 'N/A'}</p>
                <p><strong>البريد:</strong> {tenant.get('email', 'N/A') if tenant else 'N/A'}</p>
            </div>
        </div>
        
        <table class="table">
            <thead>
                <tr>
                    <th>الوصف</th>
                    <th>المبلغ</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>{record.get('description', record.get('package_name', 'اشتراك'))}</td>
                    <td>{record.get('amount', 0):,.2f} {record.get('currency', 'دج').upper()}</td>
                </tr>
            </tbody>
        </table>
        
        <div class="total">
            الإجمالي: {record.get('amount', 0):,.2f} {record.get('currency', 'دج').upper()}
        </div>
        
        <div class="footer">
            <p>شكراً لتعاملكم معنا</p>
            <p>NT Commerce - نظام إدارة نقاط البيع</p>
        </div>
    </body>
    </html>
    """
    
    return StreamingResponse(
        io.BytesIO(invoice_html.encode('utf-8')),
        media_type="text/html",
        headers={"Content-Disposition": f"inline; filename=invoice_{record.get('invoice_number', record_id)}.html"}
    )


# ============ ONLINE STORE ============

class StoreSettings(BaseModel):
    enabled: bool = False
    store_name: str = ""
    store_slug: str = ""
    description: str = ""
    logo_url: str = ""
    banner_url: str = ""
    primary_color: str = "#3b82f6"
    contact_phone: str = ""
    contact_email: str = ""
    contact_address: str = ""
    working_hours: str = "09:00 - 18:00"
    cod_enabled: bool = True
    delivery_enabled: bool = True
    min_order_amount: float = 0
    delivery_fee: float = 0
    free_delivery_threshold: float = 0

class StoreOrder(BaseModel):
    customer_name: str
    customer_phone: str
    customer_email: str = ""
    delivery_address: str
    delivery_city: str = ""
    delivery_wilaya: str = ""
    items: List[dict]
    subtotal: float
    delivery_fee: float = 0
    total: float
    notes: str = ""
    payment_method: str = "cod"  # cod = cash on delivery

@api_router.get("/store/settings")
async def get_store_settings(admin: dict = Depends(get_tenant_admin)):
    """Get store settings for tenant"""
    settings = await db.store_settings.find_one({}, {"_id": 0})
    return settings or StoreSettings().model_dump()

@api_router.put("/store/settings")
async def update_store_settings(settings: StoreSettings, admin: dict = Depends(get_tenant_admin)):
    """Update store settings"""
    tenant_id = admin.get("tenant_id")
    
    # Save settings in tenant database
    await db.store_settings.update_one(
        {},
        {"$set": settings.model_dump()},
        upsert=True
    )
    
    # Also save slug mapping in main database for public access
    if settings.store_slug and tenant_id:
        await main_db.store_slugs.update_one(
            {"tenant_id": tenant_id},
            {"$set": {
                "tenant_id": tenant_id,
                "store_slug": settings.store_slug,
                "enabled": settings.enabled,
                "store_name": settings.store_name,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }},
            upsert=True
        )
        # Also create index on store_slug for faster lookups
        await main_db.store_slugs.create_index("store_slug", unique=True, sparse=True)
    
    return {"message": "تم حفظ إعدادات المتجر"}

@api_router.get("/store/products")
async def get_store_products(admin: dict = Depends(get_tenant_admin)):
    """Get products listed in the store"""
    store_products = await db.store_products.find({}, {"_id": 0}).to_list(1000)
    return store_products

@api_router.post("/store/products")
async def add_store_product(data: dict, admin: dict = Depends(get_tenant_admin)):
    """Add product to store"""
    product_id = data.get("product_id")
    if not product_id:
        raise HTTPException(status_code=400, detail="product_id required")
    
    # Check if already added
    existing = await db.store_products.find_one({"product_id": product_id})
    if existing:
        return {"message": "Product already in store"}
    
    store_product = {
        "id": str(uuid.uuid4()),
        "product_id": product_id,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.store_products.insert_one(store_product)
    return {"message": "تمت إضافة المنتج للمتجر"}

@api_router.delete("/store/products/{product_id}")
async def remove_store_product(product_id: str, admin: dict = Depends(get_tenant_admin)):
    """Remove product from store"""
    await db.store_products.delete_one({"product_id": product_id})
    return {"message": "تمت إزالة المنتج من المتجر"}

@api_router.get("/store/orders")
async def get_store_orders(status: Optional[str] = None, admin: dict = Depends(get_tenant_admin)):
    """Get store orders"""
    query = {}
    if status:
        query["status"] = status
    orders = await db.store_orders.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    return orders

@api_router.put("/store/orders/{order_id}/status")
async def update_store_order_status(order_id: str, data: dict, admin: dict = Depends(get_tenant_admin)):
    """Update order status"""
    status = data.get("status")
    if not status:
        raise HTTPException(status_code=400, detail="status required")
    
    await db.store_orders.update_one(
        {"id": order_id},
        {"$set": {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": "تم تحديث حالة الطلب"}

# Public store endpoints (no auth required)
@api_router.get("/shop/{store_slug}")
async def get_public_store(store_slug: str):
    """Get public store by slug"""
    # Find tenant by store slug from main database
    slug_mapping = await main_db.store_slugs.find_one({"store_slug": store_slug, "enabled": True}, {"_id": 0})
    if not slug_mapping:
        raise HTTPException(status_code=404, detail="Store not found")
    
    tenant_id = slug_mapping.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=404, detail="Store not configured")
    
    # Get tenant database
    tenant_db = get_tenant_db(tenant_id)
    
    # Get store settings from tenant database
    settings = await tenant_db.store_settings.find_one({}, {"_id": 0})
    if not settings or not settings.get("enabled"):
        raise HTTPException(status_code=404, detail="Store not available")
    
    # Get store products with details
    store_products = await tenant_db.store_products.find({"is_active": True}, {"_id": 0}).to_list(1000)
    product_ids = [sp["product_id"] for sp in store_products]
    
    products = await tenant_db.products.find(
        {"id": {"$in": product_ids}, "quantity": {"$gt": 0}},
        {"_id": 0, "id": 1, "name_ar": 1, "name_en": 1, "retail_price": 1, "image_url": 1, "description_ar": 1, "description_en": 1, "quantity": 1}
    ).to_list(1000)
    
    return {
        "settings": settings,
        "products": products,
        "tenant_id": tenant_id
    }

@api_router.post("/shop/{store_slug}/order")
async def create_public_order(store_slug: str, order: StoreOrder):
    """Create order from public store (COD)"""
    # Find tenant by store slug from main database
    slug_mapping = await main_db.store_slugs.find_one({"store_slug": store_slug, "enabled": True}, {"_id": 0})
    if not slug_mapping:
        raise HTTPException(status_code=404, detail="Store not found")
    
    tenant_id = slug_mapping.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=404, detail="Store not configured")
    
    # Get tenant database
    tenant_db = get_tenant_db(tenant_id)
    
    # Validate store is enabled
    settings = await tenant_db.store_settings.find_one({"enabled": True})
    if not settings:
        raise HTTPException(status_code=404, detail="Store not available")
    
    # Validate minimum order amount
    if settings.get("min_order_amount", 0) > 0 and order.subtotal < settings["min_order_amount"]:
        raise HTTPException(status_code=400, detail=f"Minimum order amount is {settings['min_order_amount']}")
    
    # Validate products availability and update stock
    for item in order.items:
        product = await tenant_db.products.find_one({"id": item.get("product_id")})
        if not product:
            raise HTTPException(status_code=400, detail=f"Product {item.get('name', 'Unknown')} not found")
        if product.get("quantity", 0) < item.get("quantity", 1):
            raise HTTPException(status_code=400, detail=f"Product {item.get('name', product.get('name_ar', 'Unknown'))} out of stock")
    
    # Update stock for each product
    for item in order.items:
        await tenant_db.products.update_one(
            {"id": item.get("product_id")},
            {"$inc": {"quantity": -item.get("quantity", 1)}}
        )
    
    # Generate order number
    count = await tenant_db.store_orders.count_documents({}) + 1
    order_number = f"WEB{count:06d}"
    
    # Create order
    order_data = {
        "id": str(uuid.uuid4()),
        "order_number": order_number,
        "store_slug": store_slug,
        **order.model_dump(),
        "status": "pending",
        "payment_status": "unpaid",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await tenant_db.store_orders.insert_one(order_data)
    
    return {
        "message": "تم استلام طلبك بنجاح",
        "order_number": order_number,
        "order_id": order_data["id"]
    }


# ============ AUTO REPORTS API ============
@api_router.get("/auto-reports")
async def get_auto_reports(
    report_type: str = None,
    limit: int = 50,
    admin: dict = Depends(get_super_admin)
):
    query = {}
    if report_type:
        query["type"] = report_type
    reports = await main_db.auto_reports.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    return reports

@api_router.get("/auto-reports/{report_id}")
async def get_auto_report_detail(report_id: str, admin: dict = Depends(get_super_admin)):
    report = await main_db.auto_reports.find_one({"id": report_id}, {"_id": 0})
    if not report:
        raise HTTPException(status_code=404, detail="التقرير غير موجود")
    return report

@api_router.get("/collection-reports")
async def get_collection_reports(admin: dict = Depends(get_super_admin)):
    reports = await main_db.collection_reports.find({}, {"_id": 0}).sort("month", -1).limit(12).to_list(12)
    return reports

@api_router.get("/system/info")
async def get_system_info():
    """NT Commerce 12.0 - System Information"""
    return {
        "name": "NT Commerce",
        "version": "12.0.0",
        "codename": "الإصدار الأسطوري",
        "status": "running",
        "systems": {
            "bdv_original": {"tables": 58, "status": "active"},
            "nt_commerce": {"tables": 24, "status": "active"},
            "repair_system": {"tables": 16, "status": "active"},
            "defective_goods": {"tables": 11, "status": "active"},
            "ai_robots": {"tables": 14, "status": "active"},
            "security": {"tables": 9, "status": "active"},
            "backup_system": {"tables": 5, "status": "active"},
            "printing_system": {"tables": 5, "status": "active"},
            "barcode_system": {"tables": 3, "status": "active"},
            "search_system": {"tables": 3, "status": "active"},
            "performance": {"tables": 4, "status": "active"},
            "tasks_chat": {"tables": 4, "status": "active"},
            "supplier_tracking": {"tables": 2, "status": "active"},
            "wallet": {"tables": 3, "status": "active"},
        },
        "total_tables": 152,
        "robots": 6,
        "languages": ["ar", "fr"],
    }

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

# ============ LEGACY ROUTES ============
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

# Rate limiting - simple in-memory per-IP tracker
_rate_limit_store = {}
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX = 120  # max requests per window

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Basic rate limiting per IP address"""
    import time as _time
    if not request.url.path.startswith("/api/"):
        return await call_next(request)

    client_ip = request.client.host if request.client else "unknown"
    now = _time.time()

    if client_ip in _rate_limit_store:
        window_start, count = _rate_limit_store[client_ip]
        if now - window_start > RATE_LIMIT_WINDOW:
            _rate_limit_store[client_ip] = (now, 1)
        elif count >= RATE_LIMIT_MAX:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please try again later."},
                headers={"Retry-After": str(int(RATE_LIMIT_WINDOW - (now - window_start)))}
            )
        else:
            _rate_limit_store[client_ip] = (window_start, count + 1)
    else:
        _rate_limit_store[client_ip] = (now, 1)

    # Cleanup old entries periodically
    if len(_rate_limit_store) > 10000:
        cutoff = now - RATE_LIMIT_WINDOW * 2
        _rate_limit_store.clear()

    return await call_next(request)

# CORS Configuration - secure origins
_cors_env = os.environ.get('CORS_ORIGINS', '')
_cors_origins = [o.strip() for o in _cors_env.split(',') if o.strip()] if _cors_env else []
# Always allow preview URL in development
_preview_url = os.environ.get('PREVIEW_URL', '')
if _preview_url and _preview_url not in _cors_origins:
    _cors_origins.append(_preview_url)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=_cors_origins if _cors_origins else ["*"],
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
