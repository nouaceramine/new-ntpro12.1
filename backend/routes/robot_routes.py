"""
Robot Management API Routes
Control, monitor, and trigger robots
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/robots", tags=["Robots"])


def create_robot_routes(robot_manager, get_current_user):

    @router.get("/status")
    async def get_status(current_user: dict = Depends(get_current_user)):
        """Get status of all robots"""
        return robot_manager.get_status()

    @router.post("/start-all")
    async def start_all(current_user: dict = Depends(get_current_user)):
        import asyncio
        asyncio.create_task(robot_manager.start_all())
        return {"success": True, "message": "تم تشغيل جميع الروبوتات"}

    @router.post("/stop-all")
    async def stop_all(current_user: dict = Depends(get_current_user)):
        await robot_manager.stop_all()
        return {"success": True, "message": "تم إيقاف جميع الروبوتات"}

    @router.post("/restart/{robot_name}")
    async def restart_robot(robot_name: str, current_user: dict = Depends(get_current_user)):
        ok = await robot_manager.restart_robot(robot_name)
        if not ok:
            raise HTTPException(404, "الروبوت غير موجود")
        return {"success": True, "message": f"تم إعادة تشغيل {robot_name}"}

    @router.post("/run/{robot_name}")
    async def run_once(robot_name: str, report_type: Optional[str] = "daily", current_user: dict = Depends(get_current_user)):
        """Manually trigger a single run of a robot"""
        kwargs = {}
        if robot_name == "report":
            kwargs["report_type"] = report_type
        result = await robot_manager.run_robot_once(robot_name, **kwargs)
        if result is None:
            raise HTTPException(404, "الروبوت غير موجود")
        return {"success": True, "stats": result}

    @router.get("/reports")
    async def get_auto_reports(
        report_type: Optional[str] = None,
        limit: int = 20,
        current_user: dict = Depends(get_current_user),
    ):
        """Get auto-generated reports"""
        query = {}
        if current_user.get("tenant_id"):
            query["tenant_id"] = current_user["tenant_id"]
        if report_type:
            query["type"] = report_type
        from robots.robot_manager import RobotManager
        reports = await robot_manager.db.auto_reports.find(
            query, {"_id": 0}
        ).sort("created_at", -1).limit(limit).to_list(limit)
        return reports

    @router.get("/recommendations")
    async def get_reorder_recommendations(current_user: dict = Depends(get_current_user)):
        """Get inventory reorder recommendations"""
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            return []
        tid = tenant_id.replace("-", "_")
        tdb = robot_manager.client[f"tenant_{tid}"]
        recs = await tdb.reorder_recommendations.find(
            {}, {"_id": 0}
        ).sort("days_until_out", 1).to_list(50)
        return recs

    @router.get("/collection-report")
    async def get_collection_report(current_user: dict = Depends(get_current_user)):
        """Get debt collection performance report"""
        tenant_id = current_user.get("tenant_id")
        query = {"tenant_id": tenant_id} if tenant_id else {}
        reports = await robot_manager.db.collection_reports.find(
            query, {"_id": 0}
        ).sort("month", -1).limit(12).to_list(12)
        return reports

    return router
