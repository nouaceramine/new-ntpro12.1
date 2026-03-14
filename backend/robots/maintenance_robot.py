"""
Maintenance Robot
Cleans old data, optimizes indexes, monitors system health
"""
import asyncio
from datetime import datetime, timezone, timedelta
import logging

logger = logging.getLogger(__name__)


class MaintenanceRobot:
    def __init__(self, db, client, notification_service):
        self.db = db
        self.client = client
        self.notification = notification_service
        self.name = "روبوت الصيانة"
        self.is_running = False
        self.check_interval = 3600 * 24  # daily
        self.last_run = None
        self.stats = {"checks": 0, "records_cleaned": 0, "indexes_created": 0, "health_checks": 0}

    async def start(self):
        self.is_running = True
        logger.info("Maintenance Robot started")
        while self.is_running:
            try:
                await self.run_maintenance()
                self.last_run = datetime.now(timezone.utc).isoformat()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Maintenance Robot error: {e}")
                await asyncio.sleep(600)

    async def stop(self):
        self.is_running = False

    async def run_maintenance(self):
        self.stats["checks"] += 1
        await self._clean_old_notifications()
        await self._clean_old_logs()
        await self._ensure_indexes()
        await self._health_check()

    async def _clean_old_notifications(self):
        """Remove notifications older than 90 days"""
        cutoff = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()
        result = await self.db.push_notifications.delete_many({"created_at": {"$lt": cutoff}})
        if result.deleted_count:
            self.stats["records_cleaned"] += result.deleted_count
            logger.info(f"Cleaned {result.deleted_count} old notifications")

    async def _clean_old_logs(self):
        """Clean old system logs, audit logs, sms logs"""
        cutoff = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
        for collection_name in ["system_logs", "sms_log", "ai_chat_history"]:
            try:
                coll = getattr(self.db, collection_name)
                result = await coll.delete_many({"created_at": {"$lt": cutoff}})
                if result.deleted_count:
                    self.stats["records_cleaned"] += result.deleted_count
            except Exception:
                pass
        # Clean old robot data across tenants
        tenants = await self.db.saas_tenants.find({"is_active": True}, {"_id": 0, "id": 1}).to_list(500)
        cutoff_30 = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        for tenant in tenants:
            try:
                tid = tenant["id"].replace("-", "_")
                tdb = self.client[f"tenant_{tid}"]
                for coll_name in ["reorder_recommendations", "stockout_predictions", "pricing_alerts", "debt_reminders"]:
                    try:
                        result = await tdb[coll_name].delete_many({"created_at": {"$lt": cutoff_30}})
                        self.stats["records_cleaned"] += result.deleted_count
                    except Exception:
                        pass
            except Exception:
                pass

    async def _ensure_indexes(self):
        """Ensure important indexes exist on tenant databases"""
        tenants = await self.db.saas_tenants.find({"is_active": True}, {"_id": 0, "id": 1}).to_list(500)
        indexes_spec = [
            ("sales", [("created_at", -1)]),
            ("sales", [("customer_id", 1)]),
            ("sales", [("remaining", 1)]),
            ("products", [("quantity", 1)]),
            ("products", [("barcode", 1)]),
            ("customers", [("phone", 1)]),
            ("expenses", [("created_at", -1)]),
            ("purchases", [("created_at", -1)]),
        ]
        created = 0
        for tenant in tenants:
            try:
                tid = tenant["id"].replace("-", "_")
                tdb = self.client[f"tenant_{tid}"]
                for coll_name, keys in indexes_spec:
                    try:
                        await tdb[coll_name].create_index(keys, background=True)
                        created += 1
                    except Exception:
                        pass
            except Exception:
                pass
        self.stats["indexes_created"] += created

    async def _health_check(self):
        """Quick health check on database and collections"""
        self.stats["health_checks"] += 1
        try:
            tenants = await self.db.saas_tenants.count_documents({"is_active": True})
            total_users = await self.db.users.count_documents({})
            info = {
                "active_tenants": tenants,
                "admin_users": total_users,
                "checked_at": datetime.now(timezone.utc).isoformat(),
            }
            await self.db.system_health.update_one(
                {"id": "latest"},
                {"$set": {**info, "id": "latest"}},
                upsert=True,
            )
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            await self.notification.send_to_admins(
                "system",
                "تنبيه صحة النظام",
                f"فشل فحص صحة النظام: {str(e)[:100]}",
                severity="error", category="system",
            )

    async def run_once(self):
        await self.run_maintenance()
        self.last_run = datetime.now(timezone.utc).isoformat()
        return self.stats
