"""
Smart Debt Collection Robot
Tracks overdue debts, sends reminders, analyzes collection performance
"""
import asyncio
from datetime import datetime, timezone, timedelta
import logging
import uuid

logger = logging.getLogger(__name__)


class DebtRobot:
    def __init__(self, main_db, client):
        self.db = main_db
        self.client = client
        self.name = "روبوت الديون"
        self.is_running = False
        self.check_interval = 3600 * 6
        self.last_run = None
        self.stats = {"checks": 0, "reminders_sent": 0, "overdue_found": 0}

    async def start(self):
        self.is_running = True
        logger.info("Debt Robot started")
        while self.is_running:
            try:
                await self.run_checks()
                self.last_run = datetime.now(timezone.utc).isoformat()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Debt Robot error: {e}")
                await asyncio.sleep(300)

    async def stop(self):
        self.is_running = False

    async def run_checks(self):
        self.stats["checks"] += 1
        tenants = await self.db.saas_tenants.find({"is_active": True}, {"_id": 0}).to_list(500)
        for tenant in tenants:
            try:
                tid = tenant["id"].replace("-", "_")
                tdb = self.client[f"tenant_{tid}"]
                await self._check_overdue(tenant, tdb)
                await self._analyze_collection(tenant, tdb)
            except Exception as e:
                logger.error(f"Debt check failed for {tenant.get('id')}: {e}")

    async def _check_overdue(self, tenant, tdb):
        now = datetime.now(timezone.utc)
        thresholds = [
            (7, "تذكير أول", "info"),
            (14, "تذكير ثاني", "warning"),
            (30, "دين متأخر", "error"),
        ]
        for days, label, severity in thresholds:
            cutoff = (now - timedelta(days=days)).isoformat()
            overdue = await tdb.sales.find({
                "remaining": {"$gt": 0},
                "created_at": {"$lte": cutoff},
            }, {"_id": 0, "id": 1, "customer_name": 1, "remaining": 1, "created_at": 1}).to_list(200)

            if not overdue:
                continue
            self.stats["overdue_found"] += len(overdue)
            total = sum(d.get("remaining", 0) for d in overdue)

            await self.db.push_notifications.insert_one({
                "id": str(uuid.uuid4()),
                "tenant_id": tenant["id"],
                "title": f"{label} - {len(overdue)} دين",
                "message": f"ديون متأخرة +{days} يوم بقيمة {total:,.0f} دج",
                "type": severity,
                "category": "finance",
                "read_by": [],
                "created_at": now.isoformat(),
            })
            self.stats["reminders_sent"] += 1

    async def _analyze_collection(self, tenant, tdb):
        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Total outstanding debt
        debt_pipeline = [
            {"$match": {"remaining": {"$gt": 0}}},
            {"$group": {"_id": None, "total": {"$sum": "$remaining"}, "count": {"$sum": 1}}},
        ]
        debt_result = await tdb.sales.aggregate(debt_pipeline).to_list(1)
        total_debt = debt_result[0]["total"] if debt_result else 0
        debt_count = debt_result[0]["count"] if debt_result else 0

        # Payments this month
        payment_pipeline = [
            {"$match": {"created_at": {"$gte": month_start.isoformat()}, "type": {"$in": ["debt_payment", "payment"]}}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}, "count": {"$sum": 1}}},
        ]
        pay_result = await tdb.cash_box_transactions.aggregate(payment_pipeline).to_list(1)
        collected = pay_result[0]["total"] if pay_result else 0

        rate = (collected / total_debt * 100) if total_debt > 0 else 100

        await self.db.collection_reports.update_one(
            {"tenant_id": tenant["id"], "month": month_start.strftime("%Y-%m")},
            {"$set": {
                "tenant_id": tenant["id"],
                "month": month_start.strftime("%Y-%m"),
                "total_debt": round(total_debt, 2),
                "debt_count": debt_count,
                "collected": round(collected, 2),
                "collection_rate": round(rate, 2),
                "updated_at": now.isoformat(),
            }},
            upsert=True,
        )

        if rate < 30 and total_debt > 0:
            await self.db.push_notifications.insert_one({
                "id": str(uuid.uuid4()),
                "tenant_id": tenant["id"],
                "title": "تنبيه تحصيل الديون",
                "message": f"نسبة التحصيل {rate:.0f}% فقط - ديون مستحقة: {total_debt:,.0f} دج",
                "type": "error",
                "category": "finance",
                "read_by": [],
                "created_at": now.isoformat(),
            })

    async def run_once(self):
        await self.run_checks()
        self.last_run = datetime.now(timezone.utc).isoformat()
        return self.stats
