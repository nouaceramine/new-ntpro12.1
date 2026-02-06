from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt

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

# Create the main app
app = FastAPI(title="ScreenGuard Pro API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

security = HTTPBearer()

# ============ MODELS ============

class UserCreate(BaseModel):
    email: str
    password: str
    name: str
    role: str = "user"  # user or admin

class UserLogin(BaseModel):
    email: str
    password: str

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

class ProductCreate(BaseModel):
    name_en: str
    name_ar: str
    description_en: Optional[str] = ""
    description_ar: Optional[str] = ""
    price: float
    quantity: int = 0
    image_url: Optional[str] = ""
    compatible_models: List[str] = []
    low_stock_threshold: int = 10  # Custom threshold for low stock alerts

class ProductUpdate(BaseModel):
    name_en: Optional[str] = None
    name_ar: Optional[str] = None
    description_en: Optional[str] = None
    description_ar: Optional[str] = None
    price: Optional[float] = None
    quantity: Optional[int] = None
    image_url: Optional[str] = None
    compatible_models: Optional[List[str]] = None
    low_stock_threshold: Optional[int] = None

class ProductResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name_en: str
    name_ar: str
    description_en: str
    description_ar: str
    price: float
    quantity: int
    image_url: str
    compatible_models: List[str]
    low_stock_threshold: int = 10
    created_at: str
    updated_at: str

class OCRRequest(BaseModel):
    image_base64: str  # Base64 encoded image

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

# ============ AUTH ROUTES ============

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user: UserCreate):
    # Check if email exists
    existing = await db.users.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    user_doc = {
        "id": user_id,
        "email": user.email,
        "password": hash_password(user.password),
        "name": user.name,
        "role": user.role,
        "created_at": now
    }
    
    await db.users.insert_one(user_doc)
    
    access_token = create_access_token({"sub": user_id, "role": user.role})
    
    return TokenResponse(
        access_token=access_token,
        user=UserResponse(
            id=user_id,
            email=user.email,
            name=user.name,
            role=user.role,
            created_at=now
        )
    )

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    access_token = create_access_token({"sub": user["id"], "role": user["role"]})
    
    return TokenResponse(
        access_token=access_token,
        user=UserResponse(
            id=user["id"],
            email=user["email"],
            name=user["name"],
            role=user["role"],
            created_at=user["created_at"]
        )
    )

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(**current_user)

# ============ USER MANAGEMENT ROUTES (Admin Only) ============

@api_router.get("/users", response_model=List[UserResponse])
async def get_all_users(admin: dict = Depends(get_admin_user)):
    """Get all users (admin only)"""
    users = await db.users.find({}, {"_id": 0, "password": 0}).to_list(1000)
    return [UserResponse(**u) for u in users]

@api_router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, admin: dict = Depends(get_admin_user)):
    """Get a specific user (admin only)"""
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(**user)

class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None

@api_router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, updates: UserUpdate, admin: dict = Depends(get_admin_user)):
    """Update a user (admin only)"""
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
    """Delete a user (admin only)"""
    # Prevent admin from deleting themselves
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
    
    product_doc = {
        "id": product_id,
        "name_en": product.name_en,
        "name_ar": product.name_ar,
        "description_en": product.description_en or "",
        "description_ar": product.description_ar or "",
        "price": product.price,
        "quantity": product.quantity,
        "image_url": product.image_url or "",
        "compatible_models": product.compatible_models,
        "low_stock_threshold": product.low_stock_threshold,
        "created_at": now,
        "updated_at": now
    }
    
    await db.products.insert_one(product_doc)
    
    return ProductResponse(**product_doc)

@api_router.get("/products", response_model=List[ProductResponse])
async def get_products(
    search: Optional[str] = None,
    model: Optional[str] = None
):
    query = {}
    
    if search:
        # Search in name, description AND compatible_models
        query["$or"] = [
            {"name_en": {"$regex": search, "$options": "i"}},
            {"name_ar": {"$regex": search, "$options": "i"}},
            {"description_en": {"$regex": search, "$options": "i"}},
            {"description_ar": {"$regex": search, "$options": "i"}},
            {"compatible_models": {"$regex": search, "$options": "i"}}
        ]
    
    if model:
        if "$or" in query:
            query = {
                "$and": [
                    {"$or": query["$or"]},
                    {"compatible_models": {"$regex": model, "$options": "i"}}
                ]
            }
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
async def update_product(
    product_id: str,
    updates: ProductUpdate,
    admin: dict = Depends(get_admin_user)
):
    product = await db.products.find_one({"id": product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.products.update_one({"id": product_id}, {"$set": update_data})
    
    updated = await db.products.find_one({"id": product_id}, {"_id": 0})
    return ProductResponse(**updated)

@api_router.delete("/products/{product_id}")
async def delete_product(product_id: str, admin: dict = Depends(get_admin_user)):
    result = await db.products.delete_one({"id": product_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted successfully"}

# ============ STATS ROUTE ============

@api_router.get("/stats")
async def get_stats(admin: dict = Depends(get_admin_user)):
    total_products = await db.products.count_documents({})
    total_users = await db.users.count_documents({})
    
    # Count products where quantity is below their custom threshold
    pipeline = [
        {
            "$match": {
                "$expr": {
                    "$lt": ["$quantity", {"$ifNull": ["$low_stock_threshold", 10]}]
                }
            }
        },
        {"$count": "count"}
    ]
    result = await db.products.aggregate(pipeline).to_list(1)
    low_stock = result[0]["count"] if result else 0
    
    return {
        "total_products": total_products,
        "total_users": total_users,
        "low_stock_count": low_stock
    }

# ============ LOW STOCK ALERTS ============

@api_router.get("/products/alerts/low-stock", response_model=List[ProductResponse])
async def get_low_stock_products(admin: dict = Depends(get_admin_user)):
    """Get all products where quantity is below their custom threshold"""
    pipeline = [
        {
            "$match": {
                "$expr": {
                    "$lt": ["$quantity", {"$ifNull": ["$low_stock_threshold", 10]}]
                }
            }
        },
        {"$project": {"_id": 0}}
    ]
    products = await db.products.aggregate(pipeline).to_list(1000)
    return [ProductResponse(**p) for p in products]

# ============ OCR ROUTE ============

@api_router.post("/ocr/extract-models", response_model=OCRResponse)
async def extract_models_from_image(request: OCRRequest, admin: dict = Depends(get_admin_user)):
    """Extract phone model names from an image using Gemini Vision"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent
    
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="OCR service not configured")
    
    try:
        # Initialize Gemini chat
        chat = LlmChat(
            api_key=api_key,
            session_id=f"ocr-{uuid.uuid4()}",
            system_message="""You are an OCR assistant specialized in extracting phone model names from images.
            Extract all phone model names you can see in the image.
            Return ONLY the model names, one per line, without any additional text or explanation.
            Examples of model names: iPhone 15 Pro, Samsung Galaxy S24, Huawei P60 Pro, etc."""
        ).with_model("gemini", "gemini-2.5-flash")
        
        # Create image content
        image_content = ImageContent(image_base64=request.image_base64)
        
        # Send message with image
        user_message = UserMessage(
            text="Extract all phone model names from this image. Return only the model names, one per line.",
            file_contents=[image_content]
        )
        
        response = await chat.send_message(user_message)
        
        # Parse the response into a list of models
        raw_text = response.strip()
        models = [m.strip() for m in raw_text.split('\n') if m.strip()]
        
        return OCRResponse(
            extracted_models=models,
            raw_text=raw_text
        )
        
    except Exception as e:
        logger.error(f"OCR error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")

# ============ HEALTH CHECK ============

@api_router.get("/")
async def root():
    return {"message": "ScreenGuard Pro API is running"}

@api_router.get("/health")
async def health():
    return {"status": "healthy"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
