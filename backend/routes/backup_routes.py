"""
Backup System Routes
Collections: backups, backup_schedules, backup_downloads, backup_emails
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
import uuid
import json
import io
import logging

logger = logging.getLogger(__name__)


def create_backup_routes(db, main_db, get_current_user, get_tenant_admin, get_super_admin):
    router = APIRouter(prefix="/backup", tags=["backup"])

    # ── Create Backup ──
    @router.post("/create")
    async def create_backup(data: dict, admin: dict = Depends(get_tenant_admin)):
        backup_type = data.get("backup_type", "full")
        fmt = data.get("format", "json")
        collections_to_backup = data.get("collections", None)

        target_db = db
        all_collections = await target_db.list_collection_names()
        if collections_to_backup:
            all_collections = [c for c in all_collections if c in collections_to_backup]

        backup_data = {}
        total_records = 0
        for coll_name in all_collections:
            docs = await target_db[coll_name].find({}, {"_id": 0}).to_list(None)
            backup_data[coll_name] = docs
            total_records += len(docs)

        content = json.dumps(backup_data, ensure_ascii=False, default=str)
        file_size = len(content.encode("utf-8"))

        count = await main_db.backups.count_documents({}) + 1
        backup_record = {
            "id": str(uuid.uuid4()),
            "backup_number": f"BKP-{count:05d}",
            "entity_type": "tenant",
            "entity_id": admin.get("tenant_id", admin.get("id", "")),
            "entity_name": admin.get("company_name", admin.get("name", "")),
            "backup_type": backup_type,
            "format": fmt,
            "status": "completed",
            "file_name": f"backup_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json",
            "file_size": file_size,
            "tables_count": len(all_collections),
            "records_count": total_records,
            "is_encrypted": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await main_db.backups.insert_one(backup_record)
        backup_record.pop("_id", None)
        return backup_record

    @router.get("/list")
    async def get_backups(user: dict = Depends(get_current_user)):
        return await main_db.backups.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)

    @router.get("/{backup_id}")
    async def get_backup(backup_id: str, user: dict = Depends(get_current_user)):
        backup = await main_db.backups.find_one({"id": backup_id}, {"_id": 0})
        if not backup:
            raise HTTPException(status_code=404, detail="النسخة الاحتياطية غير موجودة")
        return backup

    @router.delete("/{backup_id}")
    async def delete_backup(backup_id: str, admin: dict = Depends(get_tenant_admin)):
        await main_db.backups.delete_one({"id": backup_id})
        return {"message": "تم حذف النسخة الاحتياطية"}

    @router.post("/{backup_id}/download")
    async def download_backup(backup_id: str, user: dict = Depends(get_current_user)):
        backup = await main_db.backups.find_one({"id": backup_id}, {"_id": 0})
        if not backup:
            raise HTTPException(status_code=404, detail="النسخة الاحتياطية غير موجودة")

        # Re-generate backup data for download
        target_db = db
        all_collections = await target_db.list_collection_names()
        backup_data = {}
        for coll_name in all_collections:
            docs = await target_db[coll_name].find({}, {"_id": 0}).to_list(None)
            backup_data[coll_name] = docs

        content = json.dumps(backup_data, ensure_ascii=False, default=str)
        await main_db.backup_downloads.insert_one({
            "id": str(uuid.uuid4()),
            "backup_id": backup_id,
            "entity_type": "user",
            "entity_id": user.get("id", ""),
            "downloaded_by": user.get("name", user.get("email", "")),
            "downloaded_at": datetime.now(timezone.utc).isoformat(),
        })
        return StreamingResponse(
            io.BytesIO(content.encode("utf-8")),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={backup.get('file_name', 'backup.json')}"}
        )

    # ── Restore Backup ──
    @router.post("/restore")
    async def restore_backup(data: dict, admin: dict = Depends(get_tenant_admin)):
        """Restore database from backup JSON data"""
        backup_data = data.get("backup_data")
        if not backup_data or not isinstance(backup_data, dict):
            raise HTTPException(status_code=400, detail="بيانات النسخة الاحتياطية غير صالحة")

        target_db = db
        restored_collections = 0
        restored_records = 0

        for coll_name, docs in backup_data.items():
            if not isinstance(docs, list):
                continue
            # Skip system collections
            if coll_name.startswith("system."):
                continue
            try:
                # Clear existing data
                await target_db[coll_name].delete_many({})
                if docs:
                    await target_db[coll_name].insert_many(docs)
                    restored_records += len(docs)
                restored_collections += 1
            except Exception as e:
                logger.error(f"Restore error for {coll_name}: {e}")

        # Log the restore
        await main_db.backups.insert_one({
            "id": str(uuid.uuid4()),
            "backup_number": f"RST-{await main_db.backups.count_documents({}) + 1:05d}",
            "entity_type": "tenant",
            "entity_id": admin.get("tenant_id", admin.get("id", "")),
            "entity_name": admin.get("company_name", admin.get("name", "")),
            "backup_type": "restore",
            "format": "json",
            "status": "completed",
            "file_name": "restore_operation",
            "file_size": 0,
            "tables_count": restored_collections,
            "records_count": restored_records,
            "is_encrypted": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        return {
            "message": "تم استعادة النسخة الاحتياطية بنجاح",
            "restored_collections": restored_collections,
            "restored_records": restored_records,
        }

    # ── Backup Schedules ──
    @router.post("/schedules")
    async def create_schedule(data: dict, admin: dict = Depends(get_tenant_admin)):
        schedule = {
            "id": str(uuid.uuid4()),
            "entity_type": "tenant",
            "entity_id": admin.get("tenant_id", admin.get("id", "")),
            "frequency": data.get("frequency", "daily"),
            "time": data.get("time", "02:00"),
            "format": data.get("format", "json"),
            "auto_email": data.get("auto_email", False),
            "email_to": data.get("email_to", ""),
            "keep_last": data.get("keep_last", 7),
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await main_db.backup_schedules.insert_one(schedule)
        schedule.pop("_id", None)
        return schedule

    @router.get("/schedules/list")
    async def get_schedules(user: dict = Depends(get_current_user)):
        return await main_db.backup_schedules.find({}, {"_id": 0}).to_list(50)

    @router.put("/schedules/{schedule_id}")
    async def update_schedule(schedule_id: str, data: dict, admin: dict = Depends(get_tenant_admin)):
        data.pop("id", None)
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        await main_db.backup_schedules.update_one({"id": schedule_id}, {"$set": data})
        return await main_db.backup_schedules.find_one({"id": schedule_id}, {"_id": 0})

    @router.delete("/schedules/{schedule_id}")
    async def delete_schedule(schedule_id: str, admin: dict = Depends(get_tenant_admin)):
        await main_db.backup_schedules.delete_one({"id": schedule_id})
        return {"message": "تم حذف الجدول"}

    # ── Stats ──
    @router.get("/stats/summary")
    async def get_backup_stats(user: dict = Depends(get_current_user)):
        total = await main_db.backups.count_documents({})
        size_agg = await main_db.backups.aggregate([
            {"$group": {"_id": None, "total_size": {"$sum": "$file_size"}, "total_records": {"$sum": "$records_count"}}}
        ]).to_list(1)
        schedules = await main_db.backup_schedules.count_documents({"is_active": True})
        return {
            "total_backups": total,
            "total_size": size_agg[0]["total_size"] if size_agg else 0,
            "total_records": size_agg[0]["total_records"] if size_agg else 0,
            "active_schedules": schedules,
        }

    return router
