"""
Authentication Routes
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone, timedelta
import uuid
import jwt
import bcrypt

from models.schemas import UserCreate, UserLogin, UserResponse, TokenResponse
from utils.auth import hash_password, verify_password, create_access_token, SECRET_KEY, ALGORITHM
from config.database import db, get_tenant_db, init_tenant_database

import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenResponse)
async def register(user: UserCreate):
    """Register a new user"""
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
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    """Login with email and password"""
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    stored_password = user.get("hashed_password") or user.get("password")
    if not stored_password or not verify_password(credentials.password, stored_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    access_token = create_access_token({"sub": user["id"], "role": user["role"]})
    return {"access_token": access_token, "token_type": "bearer"}
