"""
NT Commerce API Server
Main server file with organized imports from modules
"""
from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, File, UploadFile, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
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

# Try to import resend
try:
    import resend
    RESEND_AVAILABLE = True
except ImportError:
    RESEND_AVAILABLE = False

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Initialize resend if available
if RESEND_AVAILABLE:
    resend.api_key = os.environ.get('RESEND_API_KEY', '')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]  # Main SaaS database

# Multi-tenancy: Get tenant-specific database
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

# JWT Settings
SECRET_KEY = os.environ.get('JWT_SECRET', 'screenguard-secret-key-2024')
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

# ============ IMPORT MODELS FROM MODULES ============
from models.schemas import *

