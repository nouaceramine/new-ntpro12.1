"""
Smart Report Robot
Auto-generates daily/weekly/monthly reports and sends notifications
"""
import asyncio
from datetime import datetime, timezone, timedelta
import logging
import uuid

logger = logging.getLogger(__name__)


class ReportRobot:
    def __init__(self, main_db, client):
        self.db = main_db
        self.client = client
        self.name = "روبوت التقارير"
        self.is_running = False
        self.last_run = None
        self.stats = {"checks": 0, "reports_generated": 0}

    async def start(self):
        self.is_running = True
        logger.info("Report Robot started")
        while self.is_running:
            try:
                now = datetime.now(timezone.utc)
                # Daily at 08:00 UTC
                if now.hour == 8 and now.minute < 2:
                    await self.generate_daily()
                # Weekly on Sunday at 09:00
                if now.weekday() == 6 and now.hour == 9 and now.minute < 2:
                    await self.generate_weekly()
                # Monthly on 1st at 10:00
                if now.day == 1 and now.hour == 10 and now.minute < 2:
                    await self.generate_monthly()
                self.last_run = now.isoformat()
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Report Robot error: {e}")
                await asyncio.sleep(300)

    async def stop(self):
        self.is_running = False

    async def _get_tenant_stats(self, tdb, start_iso, end_iso):
        """Gather financial stats for a tenant in a date range"""
        sales_agg = await tdb.sales.aggregate([
            {"$match": {"created_at": {"$gte": start_iso, "$lte": end_iso}}},
            {"$group": {"_id": None, "total": {"$sum": "$total"}, "count": {"$sum": 1}}},
        ]).to_list(1)
        purchases_agg = await tdb.purchases.aggregate([
            {"$match": {"created_at": {"$gte": start_iso, "$lte": end_iso}}},
            {"$group": {"_id": None, "total": {"$sum": "$total"}, "count": {"$sum": 1}}},
        ]).to_list(1)
        expenses_agg = await tdb.expenses.aggregate([
            {"$match": {"created_at": {"$gte": start_iso, "$lte": end_iso}}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}, "count": {"$sum": 1}}},
        ]).to_list(1)
        sales = sales_agg[0] if sales_agg else {"total": 0, "count": 0}
        purchases = purchases_agg[0] if purchases_agg else {"total": 0, "count": 0}
        expenses = expenses_agg[0] if expenses_agg else {"total": 0, "count": 0}
        return {
            "sales_total": round(sales.get("total", 0), 2),
            "sales_count": sales.get("count", 0),
            "purchases_total": round(purchases.get("total", 0), 2),
            "purchases_count": purchases.get("count", 0),
            "expenses_total": round(expenses.get("total", 0), 2),
            "expenses_count": expenses.get("count", 0),
            "net_profit": round(sales.get("total", 0) - purchases.get("total", 0) - expenses.get("total", 0), 2),
        }

    async def _top_products(self, tdb, start_iso, end_iso, limit=5):
        pipeline = [
            {"$match": {"created_at": {"$gte": start_iso, "$lte": end_iso}}},
            {"$unwind": {"path": "$items", "preserveNullAndEmptyArrays": False}},
            {"$group": {"_id": "$items.product_id", "name": {"$first": "$items.product_name"}, "qty": {"$sum": "$items.quantity"}, "revenue": {"$sum": "$items.total"}}},
            {"$sort": {"revenue": -1}},
            {"$limit": limit},
        ]
        return await tdb.sales.aggregate(pipeline).to_list(limit)

    async def _top_customers(self, tdb, start_iso, end_iso, limit=5):
        pipeline = [
            {"$match": {"created_at": {"$gte": start_iso, "$lte": end_iso}, "customer_id": {"$ne": None}}},
            {"$group": {"_id": "$customer_id", "name": {"$first": "$customer_name"}, "total": {"$sum": "$total"}, "count": {"$sum": 1}}},
            {"$sort": {"total": -1}},
            {"$limit": limit},
        ]
        return await tdb.sales.aggregate(pipeline).to_list(limit)

    async def generate_daily(self):
        self.stats["checks"] += 1
        tenants = await self.db.saas_tenants.find({"is_active": True}, {"_id": 0}).to_list(500)
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        start = yesterday.replace(hour=0, minute=0, second=0).isoformat()
        end = yesterday.replace(hour=23, minute=59, second=59).isoformat()

        for tenant in tenants:
            try:
                tid = tenant["id"].replace("-", "_")
                tdb = self.client[f"tenant_{tid}"]
                stats = await self._get_tenant_stats(tdb, start, end)
                top_prods = await self._top_products(tdb, start, end)

                report = {
                    "id": str(uuid.uuid4()),
                    "tenant_id": tenant["id"],
                    "type": "daily",
                    "date": yesterday.strftime("%Y-%m-%d"),
                    "stats": stats,
                    "top_products": [{k: v for k, v in p.items() if k != "_id"} for p in top_prods],
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
                await self.db.auto_reports.insert_one(report)
                self.stats["reports_generated"] += 1

                await self.db.push_notifications.insert_one({
                    "id": str(uuid.uuid4()),
                    "tenant_id": tenant["id"],
                    "title": f"التقرير اليومي - {yesterday.strftime('%Y-%m-%d')}",
                    "message": f"المبيعات: {stats['sales_total']:,.0f} دج | الربح: {stats['net_profit']:,.0f} دج",
                    "type": "info",
                    "category": "reports",
                    "read_by": [],
                    "created_at": datetime.now(timezone.utc).isoformat(),
                })
            except Exception as e:
                logger.error(f"Daily report failed for {tenant.get('id')}: {e}")

    async def generate_weekly(self):
        self.stats["checks"] += 1
        tenants = await self.db.saas_tenants.find({"is_active": True}, {"_id": 0}).to_list(500)
        end_dt = datetime.now(timezone.utc) - timedelta(days=1)
        start_dt = end_dt - timedelta(days=7)
        start = start_dt.isoformat()
        end = end_dt.isoformat()

        for tenant in tenants:
            try:
                tid = tenant["id"].replace("-", "_")
                tdb = self.client[f"tenant_{tid}"]
                stats = await self._get_tenant_stats(tdb, start, end)
                top_custs = await self._top_customers(tdb, start, end)
                top_prods = await self._top_products(tdb, start, end)

                report = {
                    "id": str(uuid.uuid4()),
                    "tenant_id": tenant["id"],
                    "type": "weekly",
                    "start_date": start_dt.strftime("%Y-%m-%d"),
                    "end_date": end_dt.strftime("%Y-%m-%d"),
                    "stats": stats,
                    "top_products": [{k: v for k, v in p.items() if k != "_id"} for p in top_prods],
                    "top_customers": [{k: v for k, v in c.items() if k != "_id"} for c in top_custs],
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
                await self.db.auto_reports.insert_one(report)
                self.stats["reports_generated"] += 1
            except Exception as e:
                logger.error(f"Weekly report failed for {tenant.get('id')}: {e}")

    async def generate_monthly(self):
        self.stats["checks"] += 1
        tenants = await self.db.saas_tenants.find({"is_active": True}, {"_id": 0}).to_list(500)
        now = datetime.now(timezone.utc)
        end_dt = now.replace(day=1) - timedelta(days=1)
        start_dt = end_dt.replace(day=1, hour=0, minute=0, second=0)
        start = start_dt.isoformat()
        end = end_dt.isoformat()

        for tenant in tenants:
            try:
                tid = tenant["id"].replace("-", "_")
                tdb = self.client[f"tenant_{tid}"]
                stats = await self._get_tenant_stats(tdb, start, end)

                debt_agg = await tdb.sales.aggregate([
                    {"$match": {"remaining": {"$gt": 0}}},
                    {"$group": {"_id": None, "total": {"$sum": "$remaining"}, "count": {"$sum": 1}}},
                ]).to_list(1)
                debts = debt_agg[0] if debt_agg else {"total": 0, "count": 0}

                report = {
                    "id": str(uuid.uuid4()),
                    "tenant_id": tenant["id"],
                    "type": "monthly",
                    "month": start_dt.strftime("%Y-%m"),
                    "stats": stats,
                    "debts": {"total": round(debts.get("total", 0), 2), "count": debts.get("count", 0)},
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
                await self.db.auto_reports.insert_one(report)
                self.stats["reports_generated"] += 1

                await self.db.push_notifications.insert_one({
                    "id": str(uuid.uuid4()),
                    "tenant_id": tenant["id"],
                    "title": f"التقرير الشهري - {start_dt.strftime('%Y-%m')}",
                    "message": f"المبيعات: {stats['sales_total']:,.0f} | الربح: {stats['net_profit']:,.0f} | ديون: {debts.get('total',0):,.0f} دج",
                    "type": "info",
                    "category": "reports",
                    "read_by": [],
                    "created_at": datetime.now(timezone.utc).isoformat(),
                })
            except Exception as e:
                logger.error(f"Monthly report failed for {tenant.get('id')}: {e}")

    async def run_once(self, report_type="daily"):
        if report_type == "daily":
            await self.generate_daily()
        elif report_type == "weekly":
            await self.generate_weekly()
        elif report_type == "monthly":
            await self.generate_monthly()
        self.last_run = datetime.now(timezone.utc).isoformat()
        return self.stats
