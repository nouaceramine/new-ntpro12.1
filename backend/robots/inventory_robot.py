"""
Smart Inventory Robot
Monitors stock levels, predicts stockouts, sends alerts
"""
import asyncio
from datetime import datetime, timezone, timedelta
import logging
import uuid

logger = logging.getLogger(__name__)


class InventoryRobot:
    def __init__(self, main_db, client):
        self.db = main_db
        self.client = client
        self.name = "روبوت المخزون"
        self.is_running = False
        self.check_interval = 3600
        self.last_run = None
        self.stats = {"checks": 0, "alerts_sent": 0, "recommendations": 0}

    async def start(self):
        self.is_running = True
        logger.info("Inventory Robot started")
        while self.is_running:
            try:
                await self.run_checks()
                self.last_run = datetime.now(timezone.utc).isoformat()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Inventory Robot error: {e}")
                await asyncio.sleep(60)

    async def stop(self):
        self.is_running = False

    async def run_checks(self):
        self.stats["checks"] += 1
        tenants = await self.db.saas_tenants.find({"is_active": True}, {"_id": 0}).to_list(500)
        for tenant in tenants:
            try:
                tid = tenant["id"].replace("-", "_")
                tdb = self.client[f"tenant_{tid}"]
                await self._check_low_stock(tenant, tdb)
                await self._build_reorder_recommendations(tenant, tdb)
            except Exception as e:
                logger.error(f"Inventory check failed for {tenant.get('id')}: {e}")

    async def _check_low_stock(self, tenant, tdb):
        products = await tdb.products.find({"quantity": {"$lte": 10}}, {"_id": 0}).to_list(200)
        if not products:
            return
        for p in products[:10]:
            await self.db.push_notifications.insert_one({
                "id": str(uuid.uuid4()),
                "tenant_id": tenant["id"],
                "title": "تنبيه مخزون منخفض",
                "message": f"المنتج {p.get('name', p.get('name_ar',''))} - المخزون: {p.get('quantity', 0)}",
                "type": "warning",
                "category": "inventory",
                "read_by": [],
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
            self.stats["alerts_sent"] += 1

    async def _build_reorder_recommendations(self, tenant, tdb):
        thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        pipeline = [
            {"$match": {"created_at": {"$gte": thirty_days_ago}}},
            {"$unwind": {"path": "$items", "preserveNullAndEmptyArrays": False}},
            {"$group": {
                "_id": "$items.product_id",
                "name": {"$first": "$items.product_name"},
                "total_sold": {"$sum": "$items.quantity"},
            }},
            {"$sort": {"total_sold": -1}},
            {"$limit": 50},
        ]
        sales = await tdb.sales.aggregate(pipeline).to_list(50)
        recs = []
        for item in sales:
            prod = await tdb.products.find_one({"id": item["_id"]}, {"_id": 0, "quantity": 1, "name": 1, "name_ar": 1})
            if not prod:
                continue
            qty = prod.get("quantity", 0)
            daily_rate = item["total_sold"] / 30
            if daily_rate <= 0:
                continue
            days_left = qty / daily_rate
            if days_left < 14:
                recs.append({
                    "id": str(uuid.uuid4()),
                    "tenant_id": tenant["id"],
                    "product_id": item["_id"],
                    "product_name": item.get("name") or prod.get("name_ar", ""),
                    "current_stock": qty,
                    "daily_rate": round(daily_rate, 2),
                    "days_until_out": round(days_left, 1),
                    "recommended_order": int(daily_rate * 60),
                    "urgency": "high" if days_left < 3 else "medium" if days_left < 7 else "low",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                })
        if recs:
            await tdb.reorder_recommendations.delete_many({"tenant_id": tenant["id"]})
            await tdb.reorder_recommendations.insert_many(recs)
            self.stats["recommendations"] += len(recs)

    async def run_once(self):
        """Manual trigger for a single check cycle"""
        await self.run_checks()
        self.last_run = datetime.now(timezone.utc).isoformat()
        return self.stats
