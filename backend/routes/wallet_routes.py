"""
Wallet & Payment System Routes
Collections: wallets, wallet_transactions, wallet_transfers
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
import uuid


def create_wallet_routes(db, main_db, get_current_user, get_tenant_admin, get_super_admin):
    router = APIRouter(prefix="/wallet", tags=["wallet"])

    # ── Get Wallet ──
    @router.get("")
    async def get_wallet(user: dict = Depends(get_current_user)):
        entity_id = user.get("tenant_id", user.get("id", ""))
        entity_type = "tenant" if user.get("tenant_id") else "admin"
        wallet = await main_db.wallets.find_one(
            {"entity_id": entity_id}, {"_id": 0}
        )
        if not wallet:
            wallet = {
                "id": str(uuid.uuid4()),
                "entity_type": entity_type,
                "entity_id": entity_id,
                "balance": 0.0,
                "currency": "DZD",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            await main_db.wallets.insert_one(wallet)
            wallet.pop("_id", None)
        return wallet

    # ── Add Funds (Admin) ──
    @router.post("/add-funds")
    async def add_funds(data: dict, admin: dict = Depends(get_super_admin)):
        entity_id = data.get("entity_id", "")
        amount = data.get("amount", 0)
        if amount <= 0:
            raise HTTPException(status_code=400, detail="المبلغ يجب أن يكون أكبر من صفر")
        wallet = await main_db.wallets.find_one({"entity_id": entity_id}, {"_id": 0})
        if not wallet:
            raise HTTPException(status_code=404, detail="المحفظة غير موجودة")
        old_balance = wallet.get("balance", 0)
        new_balance = old_balance + amount
        await main_db.wallets.update_one({"entity_id": entity_id}, {"$set": {"balance": new_balance}})
        txn = {
            "id": str(uuid.uuid4()),
            "wallet_id": wallet["id"],
            "transaction_type": "credit",
            "amount": amount,
            "balance_before": old_balance,
            "balance_after": new_balance,
            "reference_type": "admin_deposit",
            "reference_id": "",
            "description": data.get("description", "إيداع إداري"),
            "status": "completed",
            "created_by": admin.get("name", admin.get("email", "")),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await main_db.wallet_transactions.insert_one(txn)
        txn.pop("_id", None)
        return {"message": "تم الإيداع", "new_balance": new_balance, "transaction": txn}

    # ── Deduct Funds ──
    @router.post("/deduct")
    async def deduct_funds(data: dict, admin: dict = Depends(get_super_admin)):
        entity_id = data.get("entity_id", "")
        amount = data.get("amount", 0)
        if amount <= 0:
            raise HTTPException(status_code=400, detail="المبلغ يجب أن يكون أكبر من صفر")
        wallet = await main_db.wallets.find_one({"entity_id": entity_id}, {"_id": 0})
        if not wallet:
            raise HTTPException(status_code=404, detail="المحفظة غير موجودة")
        old_balance = wallet.get("balance", 0)
        if old_balance < amount:
            raise HTTPException(status_code=400, detail="الرصيد غير كافي")
        new_balance = old_balance - amount
        await main_db.wallets.update_one({"entity_id": entity_id}, {"$set": {"balance": new_balance}})
        txn = {
            "id": str(uuid.uuid4()),
            "wallet_id": wallet["id"],
            "transaction_type": "debit",
            "amount": amount,
            "balance_before": old_balance,
            "balance_after": new_balance,
            "reference_type": data.get("reference_type", "admin_withdrawal"),
            "reference_id": data.get("reference_id", ""),
            "description": data.get("description", "خصم إداري"),
            "status": "completed",
            "created_by": admin.get("name", admin.get("email", "")),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await main_db.wallet_transactions.insert_one(txn)
        txn.pop("_id", None)
        return {"message": "تم الخصم", "new_balance": new_balance, "transaction": txn}

    # ── Transfers ──
    @router.post("/transfer")
    async def transfer_funds(data: dict, admin: dict = Depends(get_super_admin)):
        from_id = data.get("from_entity_id", "")
        to_id = data.get("to_entity_id", "")
        amount = data.get("amount", 0)
        fee = data.get("fee", 0)
        if amount <= 0:
            raise HTTPException(status_code=400, detail="المبلغ يجب أن يكون أكبر من صفر")

        from_wallet = await main_db.wallets.find_one({"entity_id": from_id}, {"_id": 0})
        to_wallet = await main_db.wallets.find_one({"entity_id": to_id}, {"_id": 0})
        if not from_wallet or not to_wallet:
            raise HTTPException(status_code=404, detail="محفظة غير موجودة")
        if from_wallet.get("balance", 0) < (amount + fee):
            raise HTTPException(status_code=400, detail="الرصيد غير كافي")

        from_old = from_wallet["balance"]
        to_old = to_wallet["balance"]
        net_amount = amount - fee

        await main_db.wallets.update_one({"entity_id": from_id}, {"$inc": {"balance": -(amount + fee)}})
        await main_db.wallets.update_one({"entity_id": to_id}, {"$inc": {"balance": net_amount}})

        count = await main_db.wallet_transfers.count_documents({}) + 1
        transfer = {
            "id": str(uuid.uuid4()),
            "transfer_number": f"TRF-{count:05d}",
            "from_entity_type": data.get("from_entity_type", "tenant"),
            "from_entity_id": from_id,
            "to_entity_type": data.get("to_entity_type", "tenant"),
            "to_entity_id": to_id,
            "amount": amount,
            "fee": fee,
            "net_amount": net_amount,
            "status": "completed",
            "description": data.get("description", ""),
            "created_by": admin.get("name", admin.get("email", "")),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await main_db.wallet_transfers.insert_one(transfer)
        transfer.pop("_id", None)
        return transfer

    # ── Transaction History ──
    @router.get("/transactions")
    async def get_transactions(
        entity_id: Optional[str] = None,
        transaction_type: Optional[str] = None,
        limit: int = 100,
        user: dict = Depends(get_current_user)
    ):
        if not entity_id:
            entity_id = user.get("tenant_id", user.get("id", ""))
        wallet = await main_db.wallets.find_one({"entity_id": entity_id}, {"_id": 0})
        if not wallet:
            return []
        query = {"wallet_id": wallet["id"]}
        if transaction_type:
            query["transaction_type"] = transaction_type
        return await main_db.wallet_transactions.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)

    @router.get("/transfers")
    async def get_transfers(limit: int = 50, admin: dict = Depends(get_super_admin)):
        return await main_db.wallet_transfers.find({}, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)

    # ── Stats ──
    @router.get("/stats")
    async def get_wallet_stats(admin: dict = Depends(get_super_admin)):
        total_wallets = await main_db.wallets.count_documents({})
        balance_agg = await main_db.wallets.aggregate([
            {"$group": {"_id": None, "total": {"$sum": "$balance"}}}
        ]).to_list(1)
        total_txns = await main_db.wallet_transactions.count_documents({})
        total_transfers = await main_db.wallet_transfers.count_documents({})
        return {
            "total_wallets": total_wallets,
            "total_balance": balance_agg[0]["total"] if balance_agg else 0,
            "total_transactions": total_txns,
            "total_transfers": total_transfers,
        }

    return router
