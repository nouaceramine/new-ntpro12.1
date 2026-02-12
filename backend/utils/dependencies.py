"""
FastAPI Dependencies - Shared middleware and helper functions
"""
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from config.database import db, get_tenant_db
from utils.auth import SECRET_KEY, ALGORITHM

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user from JWT token"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        tenant_id = payload.get("tenant_id")
        
        if tenant_id:
            # Tenant user
            tenant_db = get_tenant_db(tenant_id)
            user = await tenant_db.users.find_one({"id": user_id}, {"_id": 0, "password": 0, "hashed_password": 0})
        else:
            # Main system user
            user = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0, "hashed_password": 0})
        
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        user["tenant_id"] = tenant_id
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_admin_user(current_user: dict = Depends(get_current_user)):
    """Require admin role"""
    if current_user.get("role") not in ["admin", "super_admin", "manager"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

async def get_super_admin(current_user: dict = Depends(get_current_user)):
    """Require super_admin role"""
    if current_user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin access required")
    return current_user
