"""
Legacy Inline Routes - Extracted from main.py
Contains all API routes that were originally inline in the monolithic server.
These can be further modularized into separate route files.
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Literal
from datetime import datetime, timezone, timedelta
import uuid
import os
import io
import logging
import bcrypt
import jwt
import requests as http_requests

logger = logging.getLogger(__name__)


def create_legacy_routes(db, main_db, client, get_current_user, get_admin_user,
                         get_tenant_admin, require_tenant, get_super_admin, get_tenant_db,
                         hash_password, verify_password, create_access_token,
                         generate_invoice_number, init_cash_boxes, init_default_data,
                         init_tenant_database, SECRET_KEY, ALGORITHM,
                         ACCESS_TOKEN_EXPIRE_HOURS, CURRENCY, UPLOAD_DIR,
                         DEFAULT_PERMISSIONS, ROLE_DESCRIPTIONS, PERMISSION_CATEGORIES,
                         RECHARGE_CONFIG, app_logger, security,
                         # Model classes from main.py
                         UserCreate, UserLogin, UserUpdate, UserResponse,
                         TokenResponse, PasswordUpdate, PriceHistoryResponse,
                         ProductFamilyCreate, ProductFamilyUpdate, ProductFamilyResponse,
                         ProductResponse, RechargeCreate, RechargeResponse,
                         ApiKeyCreate, ApiKeyResponse, ImageOCRRequest, OCRResponse):
    """Create all legacy inline routes and return the router"""
    router = APIRouter()

    @router.post("/init-default-data")
    async def api_init_default_data(admin: dict = Depends(get_tenant_admin)):
        """Initialize default data for existing tenant"""
        tenant_db = get_tenant_db(admin["tenant_id"])
        await init_default_data(tenant_db)
        return {"message": "تم تهيئة البيانات الافتراضية بنجاح", "status": "success"}

    # ============ AUTH ROUTES ============

    @router.post("/auth/register", response_model=TokenResponse)
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

    @router.post("/auth/login", response_model=TokenResponse)
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

    @router.post("/auth/unified-login")
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

    @router.get("/auth/me", response_model=UserResponse)
    async def get_me(current_user: dict = Depends(get_current_user)):
        return UserResponse(**current_user)

    # ============ TWO-FACTOR AUTHENTICATION (2FA) ============
    import pyotp
    import qrcode
    import io
    import base64

    @router.post("/auth/2fa/setup")
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

    @router.post("/auth/2fa/verify")
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

    @router.post("/auth/2fa/disable")
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

    @router.get("/auth/2fa/status")
    async def get_2fa_status(current_user: dict = Depends(get_current_user)):
        """Check if 2FA is enabled for current user"""
        user = await main_db.users.find_one({"id": current_user["id"]}, {"_id": 0, "two_fa_enabled": 1})
        if not user:
            user = await db.users.find_one({"id": current_user["id"]}, {"_id": 0, "two_fa_enabled": 1})
        if not user:
            user = await main_db.tenants.find_one({"id": current_user["id"]}, {"_id": 0, "two_fa_enabled": 1})
        return {"enabled": user.get("two_fa_enabled", False) if user else False}

    # ============ USER MANAGEMENT ============

    @router.get("/users", response_model=List[UserResponse])
    async def get_all_users(admin: dict = Depends(get_admin_user)):
        users = await db.users.find({}, {"_id": 0, "password": 0}).to_list(1000)
        return [UserResponse(**u) for u in users]

    class UserCreateLocal(BaseModel):
        name: str
        email: str
        password: str
        role: str = "user"

    @router.post("/users", response_model=UserResponse)
    async def create_user(user_data: UserCreateLocal, admin: dict = Depends(get_admin_user)):
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

    @router.put("/users/{user_id}", response_model=UserResponse)
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

    @router.delete("/users/{user_id}")
    async def delete_user(user_id: str, admin: dict = Depends(get_admin_user)):
        if admin["id"] == user_id:
            raise HTTPException(status_code=400, detail="Cannot delete your own account")
        result = await db.users.delete_one({"id": user_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        return {"message": "User deleted successfully"}

    @router.put("/users/{user_id}/password")
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


    @router.get("/suppliers/generate-code")
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



    @router.get("/expenses/generate-code")
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

    @router.get("/inventory-sessions/generate-code")
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

    @router.get("/price-updates/generate-code")
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

    @router.get("/daily-sessions/generate-code")
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

    @router.get("/products/{product_id}/price-history", response_model=List[PriceHistoryResponse])
    async def get_product_price_history(product_id: str, user: dict = Depends(require_tenant)):
        """Get price change history for a specific product"""
        history = await db.price_history.find(
            {"product_id": product_id},
            {"_id": 0}
        ).sort("created_at", -1).to_list(100)
        return [PriceHistoryResponse(**h) for h in history]

    @router.get("/products/{product_id}/purchase-history")
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

    @router.get("/products/{product_id}/sales-history")
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

    @router.get("/price-history", response_model=List[PriceHistoryResponse])
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

    @router.get("/blacklist")
    async def get_blacklist(user: dict = Depends(require_tenant)):
        """Get all blacklisted phone numbers"""
        blacklist = await db.customer_blacklist.find({}, {"_id": 0}).sort("created_at", -1).to_list(500)
        return blacklist

    @router.post("/blacklist")
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

    @router.delete("/blacklist/{entry_id}")
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

    @router.get("/blacklist/check/{phone}")
    async def check_blacklist(phone: str, user: dict = Depends(require_tenant)):
        """Check if a phone is blacklisted"""
        entry = await db.customer_blacklist.find_one({"phone": phone}, {"_id": 0})
        return {"is_blacklisted": entry is not None, "entry": entry}

    # ============ DEBT REMINDERS ============

    class DebtReminderSettings(BaseModel):
        enabled: bool = True
        reminder_days: List[int] = [7, 14, 30]  # Days after debt to remind
        min_debt_amount: float = 1000  # Minimum debt to trigger reminder

    @router.get("/debt-reminders/settings")
    async def get_debt_reminder_settings(user: dict = Depends(require_tenant)):
        """Get debt reminder settings"""
        settings = await db.system_settings.find_one({"type": "debt_reminders"}, {"_id": 0})
        if not settings:
            return DebtReminderSettings().model_dump()
        return settings

    @router.put("/debt-reminders/settings")
    async def update_debt_reminder_settings(settings: DebtReminderSettings, user: dict = Depends(require_tenant)):
        """Update debt reminder settings"""
        await db.system_settings.update_one(
            {"type": "debt_reminders"},
            {"$set": {**settings.model_dump(), "type": "debt_reminders", "updated_at": datetime.now(timezone.utc).isoformat()}},
            upsert=True
        )
        return {"success": True, "message": "تم حفظ إعدادات التذكير"}

    @router.get("/debt-reminders/pending")
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

    @router.post("/debt-reminders/dismiss/{customer_id}")
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

    @router.get("/notifications")
    async def get_notifications(user: dict = Depends(require_tenant)):
        """Get all notifications for current user"""
        notifications = await db.notifications.find(
            {"$or": [{"user_id": user["id"]}, {"user_id": None}]},
            {"_id": 0}
        ).sort("created_at", -1).to_list(50)
        return notifications

    @router.post("/notifications")
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

    @router.put("/notifications/{notification_id}/read")
    async def mark_notification_read(notification_id: str, user: dict = Depends(require_tenant)):
        """Mark notification as read"""
        await db.notifications.update_one(
            {"id": notification_id},
            {"$set": {"is_read": True, "read_at": datetime.now(timezone.utc).isoformat()}}
        )
        return {"message": "تم تحديد الإشعار كمقروء"}

    @router.delete("/notifications/{notification_id}")
    async def delete_notification(notification_id: str, user: dict = Depends(require_tenant)):
        """Delete a notification"""
        await db.notifications.delete_one({"id": notification_id})
        return {"message": "تم حذف الإشعار"}

    @router.get("/notifications/unread-count")
    async def get_unread_notification_count(user: dict = Depends(require_tenant)):
        """Get count of unread notifications"""
        count = await db.notifications.count_documents({
            "$or": [{"user_id": user["id"]}, {"user_id": None}],
            "is_read": False
        })
        return {"count": count}

    # ============ NOTIFICATIONS ============

    @router.get("/notifications")
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

    @router.put("/notifications/{notification_id}/read")
    async def mark_notification_read(notification_id: str, user: dict = Depends(require_tenant)):
        await db.notifications.update_one(
            {"id": notification_id, "$or": [{"user_id": user["id"]}, {"user_id": {"$exists": False}}]},
            {"$set": {"read": True}}
        )
        return {"message": "Notification marked as read"}

    @router.put("/notifications/read-all")
    async def mark_all_notifications_read(user: dict = Depends(require_tenant)):
        await db.notifications.update_many(
            {"read": False, "$or": [{"user_id": user["id"]}, {"user_id": {"$exists": False}}]},
            {"$set": {"read": True}}
        )
        return {"message": "All notifications marked as read"}

    @router.post("/notifications/generate")
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

    @router.get("/products/export/excel")
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

    @router.post("/products/import/excel")
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

    @router.post("/system/selective-delete")
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

    @router.get("/settings/sidebar-order")
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

    @router.put("/settings/sidebar-order")
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

    @router.get("/notifications/settings")
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

    @router.put("/notifications/settings")
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

    @router.get("/notifications/all")
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

    @router.put("/notifications/{notification_id}/read")
    async def mark_notification_read(notification_id: str, user: dict = Depends(require_tenant)):
        """Mark a notification as read"""
        await db.notifications.update_one(
            {"id": notification_id},
            {"$set": {"read": True, "read_at": datetime.now(timezone.utc).isoformat()}}
        )
        return {"success": True}

    @router.put("/notifications/mark-all-read")
    async def mark_all_notifications_read(user: dict = Depends(require_tenant)):
        """Mark all notifications as read"""
        await db.notifications.update_many(
            {"read": False},
            {"$set": {"read": True, "read_at": datetime.now(timezone.utc).isoformat()}}
        )
        return {"success": True}

    @router.delete("/notifications/{notification_id}")
    async def delete_notification(notification_id: str, user: dict = Depends(require_tenant)):
        """Delete a notification"""
        await db.notifications.delete_one({"id": notification_id})
        return {"success": True}

    @router.delete("/notifications/clear-all")
    async def clear_all_notifications(admin: dict = Depends(get_tenant_admin)):
        """Clear all notifications"""
        result = await db.notifications.delete_many({})
        return {"success": True, "deleted_count": result.deleted_count}

    # ============ OCR ROUTE ============

    @router.post("/ocr/extract-models", response_model=OCRResponse)
    async def extract_models_from_image(request: ImageOCRRequest, admin: dict = Depends(get_tenant_admin)):
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

    @router.get("/sales/{sale_id}/invoice-pdf")
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

    @router.post("/api-keys", response_model=ApiKeyResponse)
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

    @router.get("/api-keys", response_model=List[ApiKeyResponse])
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

    @router.get("/api-keys/{key_id}")
    async def get_api_key(key_id: str, admin: dict = Depends(get_tenant_admin)):
        key = await db.api_keys.find_one({"id": key_id}, {"_id": 0})
        if not key:
            raise HTTPException(status_code=404, detail="API Key not found")
        return key

    @router.put("/api-keys/{key_id}/toggle")
    async def toggle_api_key(key_id: str, admin: dict = Depends(get_tenant_admin)):
        key = await db.api_keys.find_one({"id": key_id})
        if not key:
            raise HTTPException(status_code=404, detail="API Key not found")

        new_status = not key.get("is_active", True)
        await db.api_keys.update_one({"id": key_id}, {"$set": {"is_active": new_status}})
        return {"is_active": new_status}

    @router.delete("/api-keys/{key_id}")
    async def delete_api_key(key_id: str, admin: dict = Depends(get_tenant_admin)):
        result = await db.api_keys.delete_one({"id": key_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="API Key not found")
        return {"message": "API Key deleted successfully"}

    # ============ RECHARGE / USSD ============

    @router.get("/recharge/config")
    async def get_recharge_config(user: dict = Depends(require_tenant)):
        """Get recharge operators configuration"""
        return RECHARGE_CONFIG

    @router.post("/recharge", response_model=RechargeResponse)
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

    @router.get("/recharge", response_model=List[RechargeResponse])
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

    @router.get("/recharge/stats")
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

    @router.get("/delivery/wilayas")
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

    @router.get("/delivery/fee")
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

    @router.get("/system/settings")
    async def get_system_settings(user: dict = Depends(require_tenant)):
        """Get system settings"""
        settings = await db.system_settings.find_one({"id": "global"}, {"_id": 0})
        if not settings:
            settings = {**DEFAULT_SYSTEM_SETTINGS}
            await db.system_settings.insert_one(settings)
        else:
            settings = {k: v for k, v in settings.items() if k != "_id"}
        return settings

    @router.put("/system/settings")
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

    @router.get("/sim/slots")
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

    @router.put("/sim/slots/{slot_id}")
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

    @router.put("/sim/slots/{slot_id}/balance")
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

    @router.get("/sim/slots/{slot_id}/logs")
    async def get_sim_balance_logs(slot_id: int, admin: dict = Depends(get_tenant_admin)):
        """Get balance change history for a SIM slot"""
        logs = await db.sim_balance_logs.find({"slot_id": slot_id}, {"_id": 0}).sort("created_at", -1).to_list(50)
        return logs

    # ============ AUTO RECHARGE BY OPERATOR ============

    @router.post("/recharge/auto")
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

    # ============ WOOCOMMERCE -> routes/online_store_routes.py ============

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

    @router.get("/shipping/companies")
    async def get_shipping_companies(user: dict = Depends(require_tenant)):
        """Get list of Algerian shipping companies"""
        return ALGERIAN_SHIPPING_COMPANIES

    @router.get("/shipping/settings")
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

    @router.put("/shipping/settings/{company_id}")
    async def update_shipping_settings(company_id: str, settings: ShippingCompanySettings, admin: dict = Depends(get_tenant_admin)):
        """Update shipping company settings"""
        await db.shipping_settings.update_one(
            {"company_id": company_id},
            {"$set": settings.model_dump()},
            upsert=True
        )
        return {"message": "تم حفظ إعدادات شركة الشحن"}

    @router.post("/shipping/calculate-rate")
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

    @router.get("/shipping/wilayas")
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

    @router.get("/branding/settings")
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

    @router.put("/branding/settings")
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

    @router.get("/loyalty/settings")
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

    @router.put("/loyalty/settings")
    async def update_loyalty_settings(settings: LoyaltySettings, admin: dict = Depends(get_tenant_admin)):
        """Update loyalty program settings"""
        await db.loyalty_settings.update_one(
            {"id": "global"},
            {"$set": settings.model_dump()},
            upsert=True
        )
        return {"message": "تم تحديث إعدادات برنامج الولاء"}

    @router.get("/loyalty/customer/{customer_id}")
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

    @router.post("/loyalty/earn")
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

    @router.post("/loyalty/redeem")
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

    # ============ SMS MARKETING -> routes/sms_marketing_routes.py ============

    # ============ INVOICES ============

    class InvoiceTemplate(BaseModel):
        name: str
        type: str  # simple, detailed, thermal
        header_text: str = ""
        footer_text: str = ""
        show_logo: bool = True
        show_qr: bool = False

    @router.get("/invoices/templates")
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

    @router.post("/invoices/generate/{sale_id}")
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

    @router.get("/payments/gateways")
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

    @router.put("/payments/gateways/{gateway_id}")
    async def update_payment_gateway(gateway_id: str, settings: PaymentGatewaySettings, admin: dict = Depends(get_tenant_admin)):
        """Update payment gateway settings"""
        await db.payment_gateways.update_one(
            {"gateway": gateway_id},
            {"$set": settings.model_dump()},
            upsert=True
        )
        return {"message": "تم تحديث إعدادات بوابة الدفع"}

    # ============ SMS REMINDER -> routes/sms_marketing_routes.py ============

    # ============ ADVANCED ROLES AND PERMISSIONS ============

    @router.get("/permissions/roles")
    async def get_all_roles():
        """Get all available roles with their default permissions and descriptions"""
        return {
            "roles": list(DEFAULT_PERMISSIONS.keys()),
            "default_permissions": DEFAULT_PERMISSIONS,
            "role_descriptions": ROLE_DESCRIPTIONS,
            "permission_categories": PERMISSION_CATEGORIES
        }

    @router.get("/permissions/categories")
    async def get_permission_categories():
        """Get permission categories for UI grouping"""
        return PERMISSION_CATEGORIES

    @router.get("/permissions/role/{role_name}")
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

    @router.post("/upload/image")
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

    @router.get("/permissions/roles")
    async def get_available_roles():
        """Get all available roles and their default permissions"""
        return {
            "roles": ["admin", "manager", "user"],
            "default_permissions": DEFAULT_PERMISSIONS
        }

    @router.get("/users/{user_id}/permissions")
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

    @router.put("/users/{user_id}/permissions")
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

    @router.put("/users/{user_id}/reset-permissions")
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

    @router.post("/system/factory-reset")
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

    @router.get("/system/stats")
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

    @router.post("/products/bulk-price-update")
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

    @router.get("/products/price-preview")
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

    @router.post("/product-families", response_model=ProductFamilyResponse)
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

    @router.get("/product-families", response_model=List[ProductFamilyResponse])
    async def get_product_families(user: dict = Depends(require_tenant)):
        families = await db.product_families.find({}, {"_id": 0}).to_list(1000)

        # Update product counts
        for family in families:
            count = await db.products.count_documents({"family_id": family["id"]})
            family["product_count"] = count

        return [ProductFamilyResponse(**f) for f in families]

    @router.get("/product-families/{family_id}", response_model=ProductFamilyResponse)
    async def get_product_family(family_id: str, user: dict = Depends(require_tenant)):
        family = await db.product_families.find_one({"id": family_id}, {"_id": 0})
        if not family:
            raise HTTPException(status_code=404, detail="Product family not found")

        # Update product count
        count = await db.products.count_documents({"family_id": family_id})
        family["product_count"] = count

        return ProductFamilyResponse(**family)

    @router.put("/product-families/{family_id}", response_model=ProductFamilyResponse)
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

    @router.delete("/product-families/{family_id}")
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

    @router.get("/product-families/{family_id}/products", response_model=List[ProductResponse])
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
    @router.post("/customer-families", response_model=CustomerFamilyResponse)
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

    @router.get("/customer-families", response_model=List[CustomerFamilyResponse])
    async def get_customer_families(user: dict = Depends(require_tenant)):
        families = await db.customer_families.find({}, {"_id": 0}).to_list(100)

        # Update customer counts
        for family in families:
            count = await db.customers.count_documents({"family_id": family["id"]})
            family["customer_count"] = count

        return [CustomerFamilyResponse(**f) for f in families]

    @router.get("/customer-families/{family_id}", response_model=CustomerFamilyResponse)
    async def get_customer_family(family_id: str, user: dict = Depends(require_tenant)):
        family = await db.customer_families.find_one({"id": family_id}, {"_id": 0})
        if not family:
            raise HTTPException(status_code=404, detail="عائلة الزبائن غير موجودة")

        count = await db.customers.count_documents({"family_id": family_id})
        family["customer_count"] = count

        return CustomerFamilyResponse(**family)

    @router.put("/customer-families/{family_id}", response_model=CustomerFamilyResponse)
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

    @router.delete("/customer-families/{family_id}")
    async def delete_customer_family(family_id: str, admin: dict = Depends(get_tenant_admin)):
        count = await db.customers.count_documents({"family_id": family_id})
        if count > 0:
            raise HTTPException(status_code=400, detail=f"لا يمكن حذف عائلة بها {count} زبون")

        result = await db.customer_families.delete_one({"id": family_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="عائلة الزبائن غير موجودة")
        return {"message": "تم حذف عائلة الزبائن بنجاح"}

    # Supplier Families CRUD
    @router.post("/supplier-families", response_model=SupplierFamilyResponse)
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

    @router.get("/supplier-families", response_model=List[SupplierFamilyResponse])
    async def get_supplier_families(user: dict = Depends(require_tenant)):
        families = await db.supplier_families.find({}, {"_id": 0}).to_list(100)

        # Update supplier counts
        for family in families:
            count = await db.suppliers.count_documents({"family_id": family["id"]})
            family["supplier_count"] = count

        return [SupplierFamilyResponse(**f) for f in families]

    @router.get("/supplier-families/{family_id}", response_model=SupplierFamilyResponse)
    async def get_supplier_family(family_id: str, user: dict = Depends(require_tenant)):
        family = await db.supplier_families.find_one({"id": family_id}, {"_id": 0})
        if not family:
            raise HTTPException(status_code=404, detail="عائلة الموردين غير موجودة")

        count = await db.suppliers.count_documents({"family_id": family_id})
        family["supplier_count"] = count

        return SupplierFamilyResponse(**family)

    @router.put("/supplier-families/{family_id}", response_model=SupplierFamilyResponse)
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

    @router.delete("/supplier-families/{family_id}")
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

    @router.get("/whatsapp/settings")
    async def get_whatsapp_settings(user: dict = Depends(require_tenant)):
        """Get WhatsApp settings"""
        settings = await db.whatsapp_settings.find_one({}, {"_id": 0})
        if not settings:
            settings = {"enabled": False}
        # Don't expose access_token
        if "access_token" in settings:
            settings["access_token"] = "***" if settings["access_token"] else None
        return settings

    @router.put("/whatsapp/settings")
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

    @router.post("/whatsapp/send")
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

    @router.post("/whatsapp/notify-repair/{repair_id}")
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

    @router.get("/whatsapp/logs")
    async def get_whatsapp_logs(
        limit: int = 50,
        user: dict = Depends(require_tenant)
    ):
        """Get WhatsApp message logs"""
        logs = await db.whatsapp_logs.find({}, {"_id": 0}).sort("sent_at", -1).limit(limit).to_list(limit)
        return logs

    # ============ SPARE PARTS - PRODUCTS INTEGRATION ============

    @router.post("/spare-parts/use-in-repair")
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

    @router.post("/spare-parts/link-to-product")
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

    @router.delete("/spare-parts/unlink-product/{part_id}")
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

    @router.post("/spare-parts/sync-inventory")
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

    # ============ EMAIL REPORTS -> routes/sendgrid_email_routes.py ============

    # ============ EMAIL SETTINGS -> routes/sendgrid_email_routes.py ============

    # ============ SMART REPORTS -> routes/sendgrid_email_routes.py ============

    # ============ SAAS ROUTES MOVED TO routes/saas_routes.py ============
    # All SaaS admin routes (plans, tenants, agents, registration) have been
    # refactored to /app/backend/routes/saas_routes.py for better organization.
    # Total: 39 endpoints moved

    # ============ HEALTH CHECK ============

    @router.get("/")
    async def root():
        return {"message": "NT API is running"}

    @router.get("/health")
    async def health():
        return {"status": "healthy"}

    # ============ FEATURES MANAGEMENT ============

    @router.get("/settings/features")
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

    @router.post("/settings/features")
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

    @router.put("/users/{user_id}/permissions")
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

    @router.post("/sales/{sale_id}/log-action")
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

    @router.get("/settings/sales-permissions")
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

    @router.post("/settings/sales-permissions")
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

    @router.get("/settings/receipt")
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

    @router.post("/settings/receipt")
    async def update_receipt_settings(settings: dict, admin: dict = Depends(get_tenant_admin)):
        """Update receipt settings"""
        await db.settings.update_one(
            {"key": "receipt_settings"},
            {"$set": {"key": "receipt_settings", "value": settings}},
            upsert=True
        )
        return {"message": "Settings updated"}

    @router.get("/sales/product-tracking/{product_id}")
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

    @router.get("/system-updates/stats")
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

    @router.get("/system-updates/announcements")
    async def get_announcements(admin: dict = Depends(get_super_admin)):
        """Get all system announcements"""
        announcements = await db.system_announcements.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
        return announcements

    @router.post("/system-updates/announcements")
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

    @router.delete("/system-updates/announcements/{announcement_id}")
    async def delete_announcement(announcement_id: str, admin: dict = Depends(get_super_admin)):
        """Delete an announcement"""
        result = await db.system_announcements.delete_one({"id": announcement_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Announcement not found")

        # Also delete related notifications
        await db.notifications.delete_many({"announcement_id": announcement_id})

        return {"message": "Announcement deleted"}

    @router.post("/system-updates/push-settings")
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

    @router.get("/sync/configs")
    async def get_sync_configs(admin: dict = Depends(get_super_admin)):
        """Get all sync configurations"""
        configs = await db.sync_configs.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
        return configs

    @router.post("/sync/configs")
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

    @router.delete("/sync/configs/{config_id}")
    async def delete_sync_config(config_id: str, admin: dict = Depends(get_super_admin)):
        """Delete a sync configuration"""
        result = await db.sync_configs.delete_one({"id": config_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Config not found")
        return {"message": "Config deleted"}

    @router.post("/sync/execute")
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

    @router.get("/sync/logs")
    async def get_sync_logs(admin: dict = Depends(get_super_admin), limit: int = 50):
        """Get sync history logs"""
        logs = await db.sync_logs.find({}, {"_id": 0}).sort("created_at", -1).to_list(limit)
        return logs

    @router.get("/sync/available-types")
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

    @router.post("/sync/lock-settings")
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

    @router.get("/tenant/database-info")
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

    @router.post("/tenant/request-backup")
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

    @router.get("/tenant/export-data")
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

    # ============ SENDGRID EMAIL -> routes/sendgrid_email_routes.py ============

    # ============ STRIPE PAYMENT -> routes/stripe_routes.py ============

    # ============ ONLINE STORE -> routes/online_store_routes.py ============

    # ============ AUTO REPORTS API ============
    @router.get("/auto-reports")
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

    @router.get("/auto-reports/{report_id}")
    async def get_auto_report_detail(report_id: str, admin: dict = Depends(get_super_admin)):
        report = await main_db.auto_reports.find_one({"id": report_id}, {"_id": 0})
        if not report:
            raise HTTPException(status_code=404, detail="التقرير غير موجود")
        return report

    @router.get("/collection-reports")
    async def get_collection_reports(admin: dict = Depends(get_super_admin)):
        reports = await main_db.collection_reports.find({}, {"_id": 0}).sort("month", -1).limit(12).to_list(12)
        return reports

    @router.get("/system/info")
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


    return router
