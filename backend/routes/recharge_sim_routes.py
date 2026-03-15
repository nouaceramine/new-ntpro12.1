"""
Recharge Sim Routes - Extracted from legacy_inline_routes.py
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Literal
from datetime import datetime, timezone, timedelta
import uuid
import os
import logging


logger = logging.getLogger(__name__)


def create_recharge_sim_routes(db, require_tenant, get_tenant_admin, RECHARGE_CONFIG, RechargeCreate, RechargeResponse):
    """Create recharge sim routes"""
    router = APIRouter()

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
            slots = await db.sim_slots.find({}, {"_id": 0}).to_list(10)
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


    return router
