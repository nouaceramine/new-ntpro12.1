from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Literal
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
import io

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Settings
SECRET_KEY = os.environ.get('JWT_SECRET', 'screenguard-secret-key-2024')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

# Currency
CURRENCY = "دج"  # Algerian Dinar

# Create the main app
app = FastAPI(title="ScreenGuard Pro API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

security = HTTPBearer()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============ USER MODELS ============

class UserCreate(BaseModel):
    email: str
    password: str
    name: str
    role: str = "user"

class UserLogin(BaseModel):
    email: str
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None

class UserResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    email: str
    name: str
    role: str
    created_at: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# ============ PRODUCT MODELS ============

class ProductCreate(BaseModel):
    name_en: str
    name_ar: str
    description_en: Optional[str] = ""
    description_ar: Optional[str] = ""
    purchase_price: float = 0  # سعر الشراء
    wholesale_price: float = 0  # سعر الجملة
    retail_price: float = 0  # سعر التجزئة
    quantity: int = 0
    image_url: Optional[str] = ""
    compatible_models: List[str] = []
    low_stock_threshold: int = 10
    barcode: Optional[str] = ""

class ProductUpdate(BaseModel):
    name_en: Optional[str] = None
    name_ar: Optional[str] = None
    description_en: Optional[str] = None
    description_ar: Optional[str] = None
    purchase_price: Optional[float] = None
    wholesale_price: Optional[float] = None
    retail_price: Optional[float] = None
    quantity: Optional[int] = None
    image_url: Optional[str] = None
    compatible_models: Optional[List[str]] = None
    low_stock_threshold: Optional[int] = None
    barcode: Optional[str] = None

class ProductResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name_en: str
    name_ar: str
    description_en: str
    description_ar: str
    purchase_price: float = 0
    wholesale_price: float = 0
    retail_price: float = 0
    quantity: int
    image_url: str
    compatible_models: List[str]
    low_stock_threshold: int = 10
    barcode: str = ""
    created_at: str
    updated_at: str

# ============ CUSTOMER MODELS ============

class CustomerCreate(BaseModel):
    name: str
    phone: Optional[str] = ""
    email: Optional[str] = ""
    address: Optional[str] = ""
    notes: Optional[str] = ""

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None

class CustomerResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    phone: str
    email: str
    address: str
    notes: str
    total_purchases: float = 0
    balance: float = 0  # رصيد الزبون (دين)
    created_at: str

# ============ SUPPLIER MODELS ============

class SupplierCreate(BaseModel):
    name: str
    phone: Optional[str] = ""
    email: Optional[str] = ""
    address: Optional[str] = ""
    notes: Optional[str] = ""

class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None

class SupplierResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    phone: str
    email: str
    address: str
    notes: str
    total_purchases: float = 0
    balance: float = 0  # رصيد المورد (دين لهم)
    created_at: str

# ============ SALE MODELS ============

class SaleItem(BaseModel):
    product_id: str
    product_name: str
    quantity: int
    unit_price: float
    discount: float = 0
    total: float

class SaleCreate(BaseModel):
    customer_id: Optional[str] = None
    items: List[SaleItem]
    subtotal: float
    discount: float = 0
    total: float
    paid_amount: float
    payment_method: Literal["cash", "bank", "wallet"] = "cash"
    notes: Optional[str] = ""

class SaleResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    invoice_number: str
    customer_id: Optional[str]
    customer_name: str
    items: List[SaleItem]
    subtotal: float
    discount: float
    total: float
    paid_amount: float
    remaining: float
    payment_method: str
    status: str  # paid, partial, unpaid
    notes: str
    created_at: str
    created_by: str

# ============ PURCHASE MODELS ============

class PurchaseItem(BaseModel):
    product_id: str
    product_name: str
    quantity: int
    unit_price: float
    total: float

class PurchaseCreate(BaseModel):
    supplier_id: str
    items: List[PurchaseItem]
    total: float
    paid_amount: float
    payment_method: Literal["cash", "bank", "wallet"] = "cash"
    notes: Optional[str] = ""

class PurchaseResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    invoice_number: str
    supplier_id: str
    supplier_name: str
    items: List[PurchaseItem]
    total: float
    paid_amount: float
    remaining: float
    payment_method: str
    status: str
    notes: str
    created_at: str
    created_by: str

# ============ CASH BOX MODELS ============

class CashBoxResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    type: str  # cash, bank, wallet
    balance: float
    updated_at: str

class TransactionCreate(BaseModel):
    cash_box_id: str
    type: Literal["income", "expense", "transfer"]
    amount: float
    description: str
    reference_type: Optional[str] = None  # sale, purchase, manual
    reference_id: Optional[str] = None

class TransactionResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    cash_box_id: str
    cash_box_name: str
    type: str
    amount: float
    balance_after: float
    description: str
    reference_type: str
    reference_id: str
    created_at: str
    created_by: str

# ============ EMPLOYEE MODELS ============

class EmployeeCreate(BaseModel):
    name: str
    phone: Optional[str] = ""
    email: Optional[str] = ""
    position: Optional[str] = ""
    salary: float = 0
    hire_date: Optional[str] = None
    commission_rate: float = 0  # نسبة العمولة على المبيعات

class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    position: Optional[str] = None
    salary: Optional[float] = None
    commission_rate: Optional[float] = None

class EmployeeResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    phone: str
    email: str
    position: str
    salary: float
    hire_date: str
    commission_rate: float
    total_advances: float = 0
    total_commission: float = 0
    created_at: str

class AttendanceCreate(BaseModel):
    employee_id: str
    date: str
    status: Literal["present", "absent", "late", "leave"]
    notes: Optional[str] = ""

class AttendanceResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    employee_id: str
    employee_name: str
    date: str
    status: str
    notes: str

class AdvanceCreate(BaseModel):
    employee_id: str
    amount: float
    notes: Optional[str] = ""

class AdvanceResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    employee_id: str
    employee_name: str
    amount: float
    notes: str
    created_at: str

# ============ DEBT MODELS ============

class DebtCreate(BaseModel):
    type: Literal["receivable", "payable"]  # receivable = دين على زبون, payable = دين لمورد
    party_type: Literal["customer", "supplier"]
    party_id: str
    amount: float
    due_date: Optional[str] = None
    notes: Optional[str] = ""
    reference_type: Optional[str] = None  # sale, purchase
    reference_id: Optional[str] = None

class DebtPaymentCreate(BaseModel):
    debt_id: str
    amount: float
    payment_method: Literal["cash", "bank", "wallet"] = "cash"
    notes: Optional[str] = ""

class DebtResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    type: str
    party_type: str
    party_id: str
    party_name: str
    original_amount: float
    paid_amount: float
    remaining_amount: float
    due_date: str
    status: str  # pending, partial, paid, overdue
    notes: str
    reference_type: str
    reference_id: str
    created_at: str

class DebtPaymentResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    debt_id: str
    amount: float
    payment_method: str
    notes: str
    created_at: str
    created_by: str

# ============ API KEY MODELS ============

class ApiKeyCreate(BaseModel):
    name: str
    type: Literal["internal", "external"]  # internal = للربط مع تطبيقات أخرى, external = خدمات خارجية
    service: Optional[str] = ""  # woocommerce, stripe, etc
    key_value: Optional[str] = ""
    secret_value: Optional[str] = ""
    endpoint_url: Optional[str] = ""
    permissions: List[str] = ["read"]

class ApiKeyResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    type: str
    service: str
    key_value: str
    key_preview: str  # آخر 4 أحرف فقط
    endpoint_url: str
    permissions: List[str]
    is_active: bool
    last_used: str
    created_at: str

# ============ RECHARGE MODELS ============

class RechargeCreate(BaseModel):
    operator: Literal["mobilis", "djezzy", "ooredoo", "idoom"]
    phone_number: str
    amount: float
    recharge_type: Literal["credit", "internet", "flexy"]  # credit=رصيد, internet=أنترنت, flexy=فليكسي
    customer_id: Optional[str] = None
    payment_method: Literal["cash", "bank", "wallet"] = "cash"
    notes: Optional[str] = ""

class RechargeResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    operator: str
    phone_number: str
    amount: float
    recharge_type: str
    cost: float  # سعر التكلفة
    profit: float  # الربح
    customer_id: str
    customer_name: str
    payment_method: str
    status: str  # pending, completed, failed
    ussd_code: str
    notes: str
    created_at: str
    created_by: str

# أكواد USSD وأسعار الشحن
RECHARGE_CONFIG = {
    "mobilis": {
        "name": "موبيليس",
        "name_en": "Mobilis",
        "prefix": ["06", "05"],
        "ussd": {
            "credit": "*600*{code}#",
            "internet": "*600*{code}#",
            "balance": "*600#"
        },
        "amounts": [100, 200, 500, 1000, 2000, 5000],
        "commission": 3  # نسبة العمولة %
    },
    "djezzy": {
        "name": "جازي",
        "name_en": "Djezzy",
        "prefix": ["07"],
        "ussd": {
            "credit": "*720*{code}#",
            "flexy": "*720*3*{phone}*{amount}#",
            "balance": "*720#"
        },
        "amounts": [100, 200, 500, 1000, 2000, 5000],
        "commission": 3
    },
    "ooredoo": {
        "name": "أوريدو",
        "name_en": "Ooredoo",
        "prefix": ["05"],
        "ussd": {
            "credit": "*888*{code}#",
            "internet": "*888*{code}#",
            "balance": "*888#"
        },
        "amounts": [100, 200, 500, 1000, 2000, 5000],
        "commission": 3
    },
    "idoom": {
        "name": "إيدوم ADSL",
        "name_en": "Idoom ADSL",
        "prefix": ["0"],
        "ussd": {
            "internet": "الدفع عبر الموقع أو الوكالة",
            "balance": "https://selfcare.algerietelecom.dz"
        },
        "amounts": [1000, 1500, 2000, 2500, 3000, 4000, 5000],
        "commission": 2
    }
}

# ============ PRODUCT FAMILY MODELS ============

class ProductFamilyCreate(BaseModel):
    name_en: str
    name_ar: str
    description_en: Optional[str] = ""
    description_ar: Optional[str] = ""
    parent_id: Optional[str] = None  # للعائلات الفرعية

class ProductFamilyUpdate(BaseModel):
    name_en: Optional[str] = None
    name_ar: Optional[str] = None
    description_en: Optional[str] = None
    description_ar: Optional[str] = None
    parent_id: Optional[str] = None

class ProductFamilyResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name_en: str
    name_ar: str
    description_en: str
    description_ar: str
    parent_id: str
    parent_name: str
    product_count: int
    created_at: str

# ============ OCR & OTHER MODELS ============

class OCRRequest(BaseModel):
    image_base64: str

class OCRResponse(BaseModel):
    extracted_models: List[str]
    raw_text: str

# ============ HELPER FUNCTIONS ============

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_admin_user(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
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
    """Initialize default cash boxes if they don't exist"""
    boxes = [
        {"id": "cash", "name": "الصندوق النقدي", "type": "cash", "balance": 0},
        {"id": "bank", "name": "الحساب البنكي", "type": "bank", "balance": 0},
        {"id": "wallet", "name": "المحفظة الإلكترونية", "type": "wallet", "balance": 0}
    ]
    for box in boxes:
        existing = await db.cash_boxes.find_one({"id": box["id"]})
        if not existing:
            box["updated_at"] = datetime.now(timezone.utc).isoformat()
            await db.cash_boxes.insert_one(box)

# ============ AUTH ROUTES ============

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user: UserCreate):
    existing = await db.users.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
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
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    access_token = create_access_token({"sub": user["id"], "role": user["role"]})
    return TokenResponse(
        access_token=access_token,
        user=UserResponse(id=user["id"], email=user["email"], name=user["name"], role=user["role"], created_at=user["created_at"])
    )

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(**current_user)

# ============ USER MANAGEMENT ============

@api_router.get("/users", response_model=List[UserResponse])
async def get_all_users(admin: dict = Depends(get_admin_user)):
    users = await db.users.find({}, {"_id": 0, "password": 0}).to_list(1000)
    return [UserResponse(**u) for u in users]

@api_router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, updates: UserUpdate, admin: dict = Depends(get_admin_user)):
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
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

# ============ PRODUCT ROUTES ============

@api_router.post("/products", response_model=ProductResponse)
async def create_product(product: ProductCreate, admin: dict = Depends(get_admin_user)):
    product_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    # Check if product with same name existed before (for restock alert)
    existing = await db.products.find_one({
        "$or": [{"name_en": product.name_en}, {"name_ar": product.name_ar}]
    })
    
    product_doc = {
        "id": product_id,
        "name_en": product.name_en, "name_ar": product.name_ar,
        "description_en": product.description_en or "",
        "description_ar": product.description_ar or "",
        "purchase_price": product.purchase_price,
        "wholesale_price": product.wholesale_price,
        "retail_price": product.retail_price,
        "quantity": product.quantity,
        "image_url": product.image_url or "",
        "compatible_models": product.compatible_models,
        "low_stock_threshold": product.low_stock_threshold,
        "barcode": product.barcode or "",
        "created_at": now, "updated_at": now
    }
    await db.products.insert_one(product_doc)
    
    # Create notification if this was a restocked product
    if existing and existing.get("quantity", 0) == 0 and product.quantity > 0:
        await db.notifications.insert_one({
            "id": str(uuid.uuid4()),
            "type": "restock",
            "message_en": f"Product '{product.name_en}' is back in stock!",
            "message_ar": f"المنتج '{product.name_ar}' متوفر مرة أخرى!",
            "product_id": product_id,
            "read": False,
            "created_at": now
        })
    
    return ProductResponse(**product_doc)

@api_router.get("/products", response_model=List[ProductResponse])
async def get_products(search: Optional[str] = None, model: Optional[str] = None, barcode: Optional[str] = None):
    query = {}
    
    if barcode:
        query["barcode"] = barcode
    elif search:
        query["$or"] = [
            {"name_en": {"$regex": search, "$options": "i"}},
            {"name_ar": {"$regex": search, "$options": "i"}},
            {"description_en": {"$regex": search, "$options": "i"}},
            {"description_ar": {"$regex": search, "$options": "i"}},
            {"compatible_models": {"$regex": search, "$options": "i"}},
            {"barcode": {"$regex": search, "$options": "i"}}
        ]
    
    if model:
        if "$or" in query:
            query = {"$and": [{"$or": query["$or"]}, {"compatible_models": {"$regex": model, "$options": "i"}}]}
        else:
            query["compatible_models"] = {"$regex": model, "$options": "i"}
    
    products = await db.products.find(query, {"_id": 0}).to_list(1000)
    return [ProductResponse(**p) for p in products]

@api_router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str):
    product = await db.products.find_one({"id": product_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return ProductResponse(**product)

@api_router.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(product_id: str, updates: ProductUpdate, admin: dict = Depends(get_admin_user)):
    product = await db.products.find_one({"id": product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    old_quantity = product.get("quantity", 0)
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.products.update_one({"id": product_id}, {"$set": update_data})
    
    # Check for restock notification
    new_quantity = update_data.get("quantity", old_quantity)
    if old_quantity == 0 and new_quantity > 0:
        await db.notifications.insert_one({
            "id": str(uuid.uuid4()),
            "type": "restock",
            "message_en": f"Product '{product.get('name_en')}' is back in stock!",
            "message_ar": f"المنتج '{product.get('name_ar')}' متوفر مرة أخرى!",
            "product_id": product_id,
            "read": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    
    updated = await db.products.find_one({"id": product_id}, {"_id": 0})
    return ProductResponse(**updated)

@api_router.delete("/products/{product_id}")
async def delete_product(product_id: str, admin: dict = Depends(get_admin_user)):
    result = await db.products.delete_one({"id": product_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted successfully"}

@api_router.get("/products/alerts/low-stock", response_model=List[ProductResponse])
async def get_low_stock_products(admin: dict = Depends(get_admin_user)):
    pipeline = [
        {"$match": {"$expr": {"$lt": ["$quantity", {"$ifNull": ["$low_stock_threshold", 10]}]}}},
        {"$project": {"_id": 0}}
    ]
    products = await db.products.aggregate(pipeline).to_list(1000)
    return [ProductResponse(**p) for p in products]

# ============ CUSTOMER ROUTES ============

@api_router.post("/customers", response_model=CustomerResponse)
async def create_customer(customer: CustomerCreate, user: dict = Depends(get_current_user)):
    customer_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    customer_doc = {
        "id": customer_id, "name": customer.name,
        "phone": customer.phone or "", "email": customer.email or "",
        "address": customer.address or "", "notes": customer.notes or "",
        "total_purchases": 0, "balance": 0, "created_at": now
    }
    await db.customers.insert_one(customer_doc)
    return CustomerResponse(**customer_doc)

@api_router.get("/customers", response_model=List[CustomerResponse])
async def get_customers(search: Optional[str] = None, user: dict = Depends(get_current_user)):
    query = {}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"phone": {"$regex": search, "$options": "i"}}
        ]
    customers = await db.customers.find(query, {"_id": 0}).to_list(1000)
    return [CustomerResponse(**c) for c in customers]

@api_router.get("/customers/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: str, user: dict = Depends(get_current_user)):
    customer = await db.customers.find_one({"id": customer_id}, {"_id": 0})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return CustomerResponse(**customer)

@api_router.put("/customers/{customer_id}", response_model=CustomerResponse)
async def update_customer(customer_id: str, updates: CustomerUpdate, user: dict = Depends(get_current_user)):
    customer = await db.customers.find_one({"id": customer_id})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    if update_data:
        await db.customers.update_one({"id": customer_id}, {"$set": update_data})
    updated = await db.customers.find_one({"id": customer_id}, {"_id": 0})
    return CustomerResponse(**updated)

@api_router.delete("/customers/{customer_id}")
async def delete_customer(customer_id: str, admin: dict = Depends(get_admin_user)):
    result = await db.customers.delete_one({"id": customer_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"message": "Customer deleted successfully"}

# ============ SUPPLIER ROUTES ============

@api_router.post("/suppliers", response_model=SupplierResponse)
async def create_supplier(supplier: SupplierCreate, admin: dict = Depends(get_admin_user)):
    supplier_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    supplier_doc = {
        "id": supplier_id, "name": supplier.name,
        "phone": supplier.phone or "", "email": supplier.email or "",
        "address": supplier.address or "", "notes": supplier.notes or "",
        "total_purchases": 0, "balance": 0, "created_at": now
    }
    await db.suppliers.insert_one(supplier_doc)
    return SupplierResponse(**supplier_doc)

@api_router.get("/suppliers", response_model=List[SupplierResponse])
async def get_suppliers(search: Optional[str] = None, admin: dict = Depends(get_admin_user)):
    query = {}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"phone": {"$regex": search, "$options": "i"}}
        ]
    suppliers = await db.suppliers.find(query, {"_id": 0}).to_list(1000)
    return [SupplierResponse(**s) for s in suppliers]

@api_router.get("/suppliers/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(supplier_id: str, admin: dict = Depends(get_admin_user)):
    supplier = await db.suppliers.find_one({"id": supplier_id}, {"_id": 0})
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return SupplierResponse(**supplier)

@api_router.put("/suppliers/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(supplier_id: str, updates: SupplierUpdate, admin: dict = Depends(get_admin_user)):
    supplier = await db.suppliers.find_one({"id": supplier_id})
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    if update_data:
        await db.suppliers.update_one({"id": supplier_id}, {"$set": update_data})
    updated = await db.suppliers.find_one({"id": supplier_id}, {"_id": 0})
    return SupplierResponse(**updated)

@api_router.delete("/suppliers/{supplier_id}")
async def delete_supplier(supplier_id: str, admin: dict = Depends(get_admin_user)):
    result = await db.suppliers.delete_one({"id": supplier_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return {"message": "Supplier deleted successfully"}

# ============ SALES ROUTES ============

@api_router.post("/sales", response_model=SaleResponse)
async def create_sale(sale: SaleCreate, user: dict = Depends(get_current_user)):
    sale_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    invoice_number = await generate_invoice_number("INV")
    
    # Get customer name
    customer_name = "عميل نقدي"
    if sale.customer_id:
        customer = await db.customers.find_one({"id": sale.customer_id})
        if customer:
            customer_name = customer["name"]
    
    # Calculate remaining
    remaining = sale.total - sale.paid_amount
    status = "paid" if remaining <= 0 else ("partial" if sale.paid_amount > 0 else "unpaid")
    
    sale_doc = {
        "id": sale_id, "invoice_number": invoice_number,
        "customer_id": sale.customer_id, "customer_name": customer_name,
        "items": [item.model_dump() for item in sale.items],
        "subtotal": sale.subtotal, "discount": sale.discount, "total": sale.total,
        "paid_amount": sale.paid_amount, "remaining": max(0, remaining),
        "payment_method": sale.payment_method, "status": status,
        "notes": sale.notes or "", "created_at": now, "created_by": user["name"]
    }
    await db.sales.insert_one(sale_doc)
    
    # Update product quantities
    for item in sale.items:
        await db.products.update_one(
            {"id": item.product_id},
            {"$inc": {"quantity": -item.quantity}}
        )
        # Check for low stock notification
        product = await db.products.find_one({"id": item.product_id})
        if product:
            threshold = product.get("low_stock_threshold", 10)
            if product.get("quantity", 0) < threshold:
                await db.notifications.insert_one({
                    "id": str(uuid.uuid4()),
                    "type": "low_stock",
                    "message_en": f"Low stock alert: '{product.get('name_en')}' ({product.get('quantity')} remaining)",
                    "message_ar": f"تنبيه مخزون: '{product.get('name_ar')}' ({product.get('quantity')} متبقي)",
                    "product_id": item.product_id,
                    "read": False,
                    "created_at": now
                })
    
    # Update customer balance and total purchases
    if sale.customer_id:
        await db.customers.update_one(
            {"id": sale.customer_id},
            {"$inc": {"total_purchases": sale.total, "balance": remaining}}
        )
    
    # Update cash box
    if sale.paid_amount > 0:
        cash_box_id = sale.payment_method
        await db.cash_boxes.update_one(
            {"id": cash_box_id},
            {"$inc": {"balance": sale.paid_amount}, "$set": {"updated_at": now}}
        )
        await db.transactions.insert_one({
            "id": str(uuid.uuid4()),
            "cash_box_id": cash_box_id,
            "type": "income",
            "amount": sale.paid_amount,
            "description": f"مبيعات - فاتورة {invoice_number}",
            "reference_type": "sale",
            "reference_id": sale_id,
            "created_at": now,
            "created_by": user["name"]
        })
    
    return SaleResponse(**sale_doc)

@api_router.get("/sales", response_model=List[SaleResponse])
async def get_sales(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    customer_id: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    query = {}
    if customer_id:
        query["customer_id"] = customer_id
    if start_date:
        query["created_at"] = {"$gte": start_date}
    if end_date:
        if "created_at" in query:
            query["created_at"]["$lte"] = end_date
        else:
            query["created_at"] = {"$lte": end_date}
    
    sales = await db.sales.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return [SaleResponse(**s) for s in sales]

@api_router.get("/sales/{sale_id}", response_model=SaleResponse)
async def get_sale(sale_id: str, user: dict = Depends(get_current_user)):
    sale = await db.sales.find_one({"id": sale_id}, {"_id": 0})
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    return SaleResponse(**sale)

# Sale return/refund
@api_router.post("/sales/{sale_id}/return")
async def return_sale(sale_id: str, user: dict = Depends(get_current_user)):
    sale = await db.sales.find_one({"id": sale_id})
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    
    now = datetime.now(timezone.utc).isoformat()
    
    # Restore product quantities
    for item in sale["items"]:
        await db.products.update_one(
            {"id": item["product_id"]},
            {"$inc": {"quantity": item["quantity"]}}
        )
    
    # Update customer balance
    if sale.get("customer_id"):
        await db.customers.update_one(
            {"id": sale["customer_id"]},
            {"$inc": {"total_purchases": -sale["total"], "balance": -sale.get("remaining", 0)}}
        )
    
    # Deduct from cash box
    if sale.get("paid_amount", 0) > 0:
        await db.cash_boxes.update_one(
            {"id": sale["payment_method"]},
            {"$inc": {"balance": -sale["paid_amount"]}, "$set": {"updated_at": now}}
        )
        await db.transactions.insert_one({
            "id": str(uuid.uuid4()),
            "cash_box_id": sale["payment_method"],
            "type": "expense",
            "amount": sale["paid_amount"],
            "description": f"إرجاع مبيعات - فاتورة {sale['invoice_number']}",
            "reference_type": "return",
            "reference_id": sale_id,
            "created_at": now,
            "created_by": user["name"]
        })
    
    # Mark sale as returned
    await db.sales.update_one({"id": sale_id}, {"$set": {"status": "returned"}})
    
    return {"message": "Sale returned successfully"}

# ============ PURCHASE ROUTES ============

@api_router.post("/purchases", response_model=PurchaseResponse)
async def create_purchase(purchase: PurchaseCreate, admin: dict = Depends(get_admin_user)):
    purchase_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    invoice_number = await generate_invoice_number("PUR")
    
    supplier = await db.suppliers.find_one({"id": purchase.supplier_id})
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    remaining = purchase.total - purchase.paid_amount
    status = "paid" if remaining <= 0 else ("partial" if purchase.paid_amount > 0 else "unpaid")
    
    purchase_doc = {
        "id": purchase_id, "invoice_number": invoice_number,
        "supplier_id": purchase.supplier_id, "supplier_name": supplier["name"],
        "items": [item.model_dump() for item in purchase.items],
        "total": purchase.total, "paid_amount": purchase.paid_amount,
        "remaining": max(0, remaining), "payment_method": purchase.payment_method,
        "status": status, "notes": purchase.notes or "",
        "created_at": now, "created_by": admin["name"]
    }
    await db.purchases.insert_one(purchase_doc)
    
    # Update product quantities and check for restock notifications
    for item in purchase.items:
        product = await db.products.find_one({"id": item.product_id})
        old_quantity = product.get("quantity", 0) if product else 0
        
        await db.products.update_one(
            {"id": item.product_id},
            {"$inc": {"quantity": item.quantity}}
        )
        
        # Create restock notification if product was out of stock
        if old_quantity == 0 and item.quantity > 0 and product:
            await db.notifications.insert_one({
                "id": str(uuid.uuid4()),
                "type": "restock",
                "message_en": f"Product '{product.get('name_en')}' is back in stock!",
                "message_ar": f"المنتج '{product.get('name_ar')}' متوفر مرة أخرى!",
                "product_id": item.product_id,
                "read": False,
                "created_at": now
            })
    
    # Update supplier balance
    await db.suppliers.update_one(
        {"id": purchase.supplier_id},
        {"$inc": {"total_purchases": purchase.total, "balance": remaining}}
    )
    
    # Update cash box
    if purchase.paid_amount > 0:
        await db.cash_boxes.update_one(
            {"id": purchase.payment_method},
            {"$inc": {"balance": -purchase.paid_amount}, "$set": {"updated_at": now}}
        )
        await db.transactions.insert_one({
            "id": str(uuid.uuid4()),
            "cash_box_id": purchase.payment_method,
            "type": "expense",
            "amount": purchase.paid_amount,
            "description": f"مشتريات - فاتورة {invoice_number}",
            "reference_type": "purchase",
            "reference_id": purchase_id,
            "created_at": now,
            "created_by": admin["name"]
        })
    
    return PurchaseResponse(**purchase_doc)

@api_router.get("/purchases", response_model=List[PurchaseResponse])
async def get_purchases(supplier_id: Optional[str] = None, admin: dict = Depends(get_admin_user)):
    query = {}
    if supplier_id:
        query["supplier_id"] = supplier_id
    purchases = await db.purchases.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return [PurchaseResponse(**p) for p in purchases]

# ============ CASH BOX ROUTES ============

@api_router.get("/cash-boxes", response_model=List[CashBoxResponse])
async def get_cash_boxes(admin: dict = Depends(get_admin_user)):
    await init_cash_boxes()
    boxes = await db.cash_boxes.find({}, {"_id": 0}).to_list(100)
    return [CashBoxResponse(**b) for b in boxes]

@api_router.post("/cash-boxes/transfer")
async def transfer_between_boxes(
    from_box: str, to_box: str, amount: float,
    admin: dict = Depends(get_admin_user)
):
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    from_cash_box = await db.cash_boxes.find_one({"id": from_box})
    if not from_cash_box or from_cash_box["balance"] < amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    now = datetime.now(timezone.utc).isoformat()
    
    # Deduct from source
    await db.cash_boxes.update_one(
        {"id": from_box},
        {"$inc": {"balance": -amount}, "$set": {"updated_at": now}}
    )
    
    # Add to destination
    await db.cash_boxes.update_one(
        {"id": to_box},
        {"$inc": {"balance": amount}, "$set": {"updated_at": now}}
    )
    
    # Record transactions
    transfer_id = str(uuid.uuid4())
    await db.transactions.insert_many([
        {
            "id": str(uuid.uuid4()),
            "cash_box_id": from_box,
            "type": "expense",
            "amount": amount,
            "description": f"تحويل إلى {to_box}",
            "reference_type": "transfer",
            "reference_id": transfer_id,
            "created_at": now,
            "created_by": admin["name"]
        },
        {
            "id": str(uuid.uuid4()),
            "cash_box_id": to_box,
            "type": "income",
            "amount": amount,
            "description": f"تحويل من {from_box}",
            "reference_type": "transfer",
            "reference_id": transfer_id,
            "created_at": now,
            "created_by": admin["name"]
        }
    ])
    
    return {"message": "Transfer completed successfully"}

@api_router.get("/transactions", response_model=List[TransactionResponse])
async def get_transactions(
    cash_box_id: Optional[str] = None,
    type: Optional[str] = None,
    admin: dict = Depends(get_admin_user)
):
    query = {}
    if cash_box_id:
        query["cash_box_id"] = cash_box_id
    if type:
        query["type"] = type
    
    transactions = await db.transactions.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    # Get cash box names
    cash_boxes = {b["id"]: b["name"] for b in await db.cash_boxes.find({}, {"_id": 0}).to_list(100)}
    
    result = []
    for t in transactions:
        t["cash_box_name"] = cash_boxes.get(t["cash_box_id"], t["cash_box_id"])
        t["balance_after"] = 0  # Calculate if needed
        result.append(TransactionResponse(**t))
    
    return result

# ============ NOTIFICATIONS ============

@api_router.get("/notifications")
async def get_notifications(user: dict = Depends(get_current_user)):
    notifications = await db.notifications.find(
        {"read": False}, {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    return notifications

@api_router.put("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, user: dict = Depends(get_current_user)):
    await db.notifications.update_one({"id": notification_id}, {"$set": {"read": True}})
    return {"message": "Notification marked as read"}

@api_router.put("/notifications/read-all")
async def mark_all_notifications_read(user: dict = Depends(get_current_user)):
    await db.notifications.update_many({"read": False}, {"$set": {"read": True}})
    return {"message": "All notifications marked as read"}

# ============ STATS & REPORTS ============

@api_router.get("/stats")
async def get_stats(admin: dict = Depends(get_admin_user)):
    await init_cash_boxes()
    
    total_products = await db.products.count_documents({})
    total_customers = await db.customers.count_documents({})
    total_suppliers = await db.suppliers.count_documents({})
    total_employees = await db.employees.count_documents({})
    
    # Low stock count
    pipeline = [
        {"$match": {"$expr": {"$lt": ["$quantity", {"$ifNull": ["$low_stock_threshold", 10]}]}}},
        {"$count": "count"}
    ]
    result = await db.products.aggregate(pipeline).to_list(1)
    low_stock = result[0]["count"] if result else 0
    
    # Today's sales
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    today_sales = await db.sales.aggregate([
        {"$match": {"created_at": {"$gte": today}, "status": {"$ne": "returned"}}},
        {"$group": {"_id": None, "total": {"$sum": "$total"}, "count": {"$sum": 1}}}
    ]).to_list(1)
    
    # Cash boxes
    cash_boxes = await db.cash_boxes.find({}, {"_id": 0}).to_list(100)
    total_cash = sum(b.get("balance", 0) for b in cash_boxes)
    
    # Unread notifications
    unread_notifications = await db.notifications.count_documents({"read": False})
    
    # Total debts
    total_receivables = await db.debts.aggregate([
        {"$match": {"type": "receivable", "status": {"$ne": "paid"}}},
        {"$group": {"_id": None, "total": {"$sum": "$remaining_amount"}}}
    ]).to_list(1)
    
    total_payables = await db.debts.aggregate([
        {"$match": {"type": "payable", "status": {"$ne": "paid"}}},
        {"$group": {"_id": None, "total": {"$sum": "$remaining_amount"}}}
    ]).to_list(1)
    
    return {
        "total_products": total_products,
        "total_customers": total_customers,
        "total_suppliers": total_suppliers,
        "total_employees": total_employees,
        "low_stock_count": low_stock,
        "today_sales_total": today_sales[0]["total"] if today_sales else 0,
        "today_sales_count": today_sales[0]["count"] if today_sales else 0,
        "total_cash": total_cash,
        "cash_boxes": cash_boxes,
        "unread_notifications": unread_notifications,
        "total_receivables": total_receivables[0]["total"] if total_receivables else 0,
        "total_payables": total_payables[0]["total"] if total_payables else 0,
        "currency": CURRENCY
    }

# ============ CHARTS & ANALYTICS ============

@api_router.get("/reports/sales-chart")
async def get_sales_chart(days: int = 7, admin: dict = Depends(get_admin_user)):
    """Get sales data for chart (last N days)"""
    start_date = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    
    pipeline = [
        {"$match": {"created_at": {"$gte": start_date}, "status": {"$ne": "returned"}}},
        {"$addFields": {"date": {"$substr": ["$created_at", 0, 10]}}},
        {"$group": {
            "_id": "$date",
            "total_sales": {"$sum": "$total"},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]
    
    result = await db.sales.aggregate(pipeline).to_list(100)
    return [{"date": r["_id"], "total": r["total_sales"], "count": r["count"]} for r in result]

@api_router.get("/reports/top-products")
async def get_top_products(limit: int = 10, admin: dict = Depends(get_admin_user)):
    """Get top selling products"""
    pipeline = [
        {"$match": {"status": {"$ne": "returned"}}},
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
    
    result = await db.sales.aggregate(pipeline).to_list(limit)
    return result

@api_router.get("/reports/top-customers")
async def get_top_customers(limit: int = 10, admin: dict = Depends(get_admin_user)):
    """Get top customers by purchases"""
    customers = await db.customers.find(
        {}, {"_id": 0}
    ).sort("total_purchases", -1).limit(limit).to_list(limit)
    return customers

@api_router.get("/reports/profit")
async def get_profit_report(days: int = 30, admin: dict = Depends(get_admin_user)):
    """Get profit report"""
    start_date = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    
    # Get sales
    sales = await db.sales.find(
        {"created_at": {"$gte": start_date}, "status": {"$ne": "returned"}},
        {"_id": 0, "items": 1, "total": 1}
    ).to_list(10000)
    
    total_revenue = sum(s["total"] for s in sales)
    
    # Calculate cost from items (need to get purchase prices from products)
    total_cost = 0
    for sale in sales:
        for item in sale.get("items", []):
            product = await db.products.find_one({"id": item["product_id"]}, {"_id": 0, "purchase_price": 1})
            if product:
                total_cost += product.get("purchase_price", 0) * item["quantity"]
    
    gross_profit = total_revenue - total_cost
    profit_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    return {
        "total_revenue": total_revenue,
        "total_cost": total_cost,
        "gross_profit": gross_profit,
        "profit_margin": round(profit_margin, 2),
        "period_days": days
    }

# ============ EMPLOYEE ROUTES ============

@api_router.post("/employees", response_model=EmployeeResponse)
async def create_employee(employee: EmployeeCreate, admin: dict = Depends(get_admin_user)):
    employee_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    employee_doc = {
        "id": employee_id,
        "name": employee.name,
        "phone": employee.phone or "",
        "email": employee.email or "",
        "position": employee.position or "",
        "salary": employee.salary,
        "hire_date": employee.hire_date or now[:10],
        "commission_rate": employee.commission_rate,
        "total_advances": 0,
        "total_commission": 0,
        "created_at": now
    }
    await db.employees.insert_one(employee_doc)
    return EmployeeResponse(**employee_doc)

@api_router.get("/employees", response_model=List[EmployeeResponse])
async def get_employees(admin: dict = Depends(get_admin_user)):
    employees = await db.employees.find({}, {"_id": 0}).to_list(1000)
    return [EmployeeResponse(**e) for e in employees]

@api_router.get("/employees/{employee_id}", response_model=EmployeeResponse)
async def get_employee(employee_id: str, admin: dict = Depends(get_admin_user)):
    employee = await db.employees.find_one({"id": employee_id}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return EmployeeResponse(**employee)

@api_router.put("/employees/{employee_id}", response_model=EmployeeResponse)
async def update_employee(employee_id: str, updates: EmployeeUpdate, admin: dict = Depends(get_admin_user)):
    employee = await db.employees.find_one({"id": employee_id})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    if update_data:
        await db.employees.update_one({"id": employee_id}, {"$set": update_data})
    updated = await db.employees.find_one({"id": employee_id}, {"_id": 0})
    return EmployeeResponse(**updated)

@api_router.delete("/employees/{employee_id}")
async def delete_employee(employee_id: str, admin: dict = Depends(get_admin_user)):
    result = await db.employees.delete_one({"id": employee_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"message": "Employee deleted successfully"}

# Attendance
@api_router.post("/employees/attendance", response_model=AttendanceResponse)
async def record_attendance(attendance: AttendanceCreate, admin: dict = Depends(get_admin_user)):
    employee = await db.employees.find_one({"id": attendance.employee_id}, {"_id": 0, "name": 1})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    attendance_id = str(uuid.uuid4())
    attendance_doc = {
        "id": attendance_id,
        "employee_id": attendance.employee_id,
        "employee_name": employee["name"],
        "date": attendance.date,
        "status": attendance.status,
        "notes": attendance.notes or ""
    }
    await db.attendance.insert_one(attendance_doc)
    return AttendanceResponse(**attendance_doc)

@api_router.get("/employees/{employee_id}/attendance")
async def get_employee_attendance(employee_id: str, month: Optional[str] = None, admin: dict = Depends(get_admin_user)):
    query = {"employee_id": employee_id}
    if month:
        query["date"] = {"$regex": f"^{month}"}
    attendance = await db.attendance.find(query, {"_id": 0}).sort("date", -1).to_list(100)
    return attendance

# Advances (سلف)
@api_router.post("/employees/advances", response_model=AdvanceResponse)
async def create_advance(advance: AdvanceCreate, admin: dict = Depends(get_admin_user)):
    employee = await db.employees.find_one({"id": advance.employee_id}, {"_id": 0, "name": 1})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    now = datetime.now(timezone.utc).isoformat()
    advance_id = str(uuid.uuid4())
    
    advance_doc = {
        "id": advance_id,
        "employee_id": advance.employee_id,
        "employee_name": employee["name"],
        "amount": advance.amount,
        "notes": advance.notes or "",
        "created_at": now
    }
    await db.advances.insert_one(advance_doc)
    
    # Update employee total advances
    await db.employees.update_one(
        {"id": advance.employee_id},
        {"$inc": {"total_advances": advance.amount}}
    )
    
    return AdvanceResponse(**advance_doc)

@api_router.get("/employees/{employee_id}/advances")
async def get_employee_advances(employee_id: str, admin: dict = Depends(get_admin_user)):
    advances = await db.advances.find({"employee_id": employee_id}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return advances

# ============ DEBT ROUTES ============

@api_router.post("/debts", response_model=DebtResponse)
async def create_debt(debt: DebtCreate, admin: dict = Depends(get_admin_user)):
    # Get party name
    if debt.party_type == "customer":
        party = await db.customers.find_one({"id": debt.party_id}, {"_id": 0, "name": 1})
    else:
        party = await db.suppliers.find_one({"id": debt.party_id}, {"_id": 0, "name": 1})
    
    if not party:
        raise HTTPException(status_code=404, detail="Party not found")
    
    now = datetime.now(timezone.utc).isoformat()
    debt_id = str(uuid.uuid4())
    
    debt_doc = {
        "id": debt_id,
        "type": debt.type,
        "party_type": debt.party_type,
        "party_id": debt.party_id,
        "party_name": party["name"],
        "original_amount": debt.amount,
        "paid_amount": 0,
        "remaining_amount": debt.amount,
        "due_date": debt.due_date or "",
        "status": "pending",
        "notes": debt.notes or "",
        "reference_type": debt.reference_type or "",
        "reference_id": debt.reference_id or "",
        "created_at": now
    }
    await db.debts.insert_one(debt_doc)
    return DebtResponse(**debt_doc)

@api_router.get("/debts", response_model=List[DebtResponse])
async def get_debts(
    type: Optional[str] = None,
    party_type: Optional[str] = None,
    status: Optional[str] = None,
    admin: dict = Depends(get_admin_user)
):
    query = {}
    if type:
        query["type"] = type
    if party_type:
        query["party_type"] = party_type
    if status:
        query["status"] = status
    
    debts = await db.debts.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    # Check for overdue
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for debt in debts:
        if debt.get("due_date") and debt["due_date"] < today and debt["status"] not in ["paid", "overdue"]:
            await db.debts.update_one({"id": debt["id"]}, {"$set": {"status": "overdue"}})
            debt["status"] = "overdue"
    
    return [DebtResponse(**d) for d in debts]

@api_router.post("/debts/{debt_id}/pay", response_model=DebtPaymentResponse)
async def pay_debt(debt_id: str, payment: DebtPaymentCreate, admin: dict = Depends(get_admin_user)):
    debt = await db.debts.find_one({"id": debt_id})
    if not debt:
        raise HTTPException(status_code=404, detail="Debt not found")
    
    if payment.amount > debt["remaining_amount"]:
        raise HTTPException(status_code=400, detail="Payment amount exceeds remaining debt")
    
    now = datetime.now(timezone.utc).isoformat()
    payment_id = str(uuid.uuid4())
    
    new_paid = debt["paid_amount"] + payment.amount
    new_remaining = debt["remaining_amount"] - payment.amount
    new_status = "paid" if new_remaining <= 0 else "partial"
    
    # Update debt
    await db.debts.update_one(
        {"id": debt_id},
        {"$set": {
            "paid_amount": new_paid,
            "remaining_amount": new_remaining,
            "status": new_status
        }}
    )
    
    # Record payment
    payment_doc = {
        "id": payment_id,
        "debt_id": debt_id,
        "amount": payment.amount,
        "payment_method": payment.payment_method,
        "notes": payment.notes or "",
        "created_at": now,
        "created_by": admin["name"]
    }
    await db.debt_payments.insert_one(payment_doc)
    
    # Update cash box
    tx_type = "income" if debt["type"] == "receivable" else "expense"
    await db.cash_boxes.update_one(
        {"id": payment.payment_method},
        {"$inc": {"balance": payment.amount if tx_type == "income" else -payment.amount}, "$set": {"updated_at": now}}
    )
    
    await db.transactions.insert_one({
        "id": str(uuid.uuid4()),
        "cash_box_id": payment.payment_method,
        "type": tx_type,
        "amount": payment.amount,
        "description": f"سداد دين - {debt['party_name']}",
        "reference_type": "debt_payment",
        "reference_id": payment_id,
        "created_at": now,
        "created_by": admin["name"]
    })
    
    return DebtPaymentResponse(**payment_doc)

@api_router.get("/debts/{debt_id}/payments")
async def get_debt_payments(debt_id: str, admin: dict = Depends(get_admin_user)):
    payments = await db.debt_payments.find({"debt_id": debt_id}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return payments

# ============ EXCEL IMPORT/EXPORT ============

@api_router.get("/products/export/excel")
async def export_products_excel(admin: dict = Depends(get_admin_user)):
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
async def import_products_excel(file: UploadFile = File(...), admin: dict = Depends(get_admin_user)):
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

# ============ BACKUP ============

@api_router.get("/backup/create")
async def create_backup(admin: dict = Depends(get_admin_user)):
    """Create a backup of all data"""
    import json
    
    collections = ["users", "products", "customers", "suppliers", "sales", "purchases", 
                   "cash_boxes", "transactions", "employees", "attendance", "advances", 
                   "debts", "debt_payments", "notifications"]
    
    backup_data = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "collections": {}
    }
    
    for collection_name in collections:
        collection = db[collection_name]
        docs = await collection.find({}, {"_id": 0}).to_list(100000)
        backup_data["collections"][collection_name] = docs
    
    output = io.BytesIO()
    output.write(json.dumps(backup_data, ensure_ascii=False, indent=2).encode('utf-8'))
    output.seek(0)
    
    filename = f"backup_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    
    return StreamingResponse(
        output,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# ============ OCR ROUTE ============

@api_router.post("/ocr/extract-models", response_model=OCRResponse)
async def extract_models_from_image(request: OCRRequest, admin: dict = Depends(get_admin_user)):
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
async def get_invoice_pdf(sale_id: str, user: dict = Depends(get_current_user)):
    sale = await db.sales.find_one({"id": sale_id}, {"_id": 0})
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    
    # Generate simple HTML invoice
    items_html = ""
    for i, item in enumerate(sale["items"], 1):
        items_html += f"""
        <tr>
            <td>{i}</td>
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
            .info {{ display: flex; justify-content: space-between; margin-bottom: 20px; }}
            .info div {{ width: 48%; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 10px; text-align: right; }}
            th {{ background: #2563EB; color: white; }}
            .totals {{ text-align: left; margin-top: 20px; }}
            .totals table {{ width: 300px; margin-right: 0; margin-left: auto; }}
            .footer {{ text-align: center; margin-top: 40px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>سكرين جارد برو</h1>
            <p>فاتورة مبيعات</p>
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
async def create_api_key(api_key: ApiKeyCreate, admin: dict = Depends(get_admin_user)):
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
async def get_api_keys(admin: dict = Depends(get_admin_user)):
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
async def get_api_key(key_id: str, admin: dict = Depends(get_admin_user)):
    key = await db.api_keys.find_one({"id": key_id}, {"_id": 0})
    if not key:
        raise HTTPException(status_code=404, detail="API Key not found")
    return key

@api_router.put("/api-keys/{key_id}/toggle")
async def toggle_api_key(key_id: str, admin: dict = Depends(get_admin_user)):
    key = await db.api_keys.find_one({"id": key_id})
    if not key:
        raise HTTPException(status_code=404, detail="API Key not found")
    
    new_status = not key.get("is_active", True)
    await db.api_keys.update_one({"id": key_id}, {"$set": {"is_active": new_status}})
    return {"is_active": new_status}

@api_router.delete("/api-keys/{key_id}")
async def delete_api_key(key_id: str, admin: dict = Depends(get_admin_user)):
    result = await db.api_keys.delete_one({"id": key_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="API Key not found")
    return {"message": "API Key deleted successfully"}

# ============ RECHARGE / USSD ============

@api_router.get("/recharge/config")
async def get_recharge_config(user: dict = Depends(get_current_user)):
    """Get recharge operators configuration"""
    return RECHARGE_CONFIG

@api_router.post("/recharge", response_model=RechargeResponse)
async def create_recharge(recharge: RechargeCreate, user: dict = Depends(get_current_user)):
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
    user: dict = Depends(get_current_user)
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
async def get_recharge_stats(days: int = 30, admin: dict = Depends(get_admin_user)):
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

# ============ HEALTH CHECK ============

@api_router.get("/")
async def root():
    return {"message": "ScreenGuard Pro API is running"}

@api_router.get("/health")
async def health():
    return {"status": "healthy"}

# Include router and middleware
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    await init_cash_boxes()

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
