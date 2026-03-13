"""
Central Robot Manager
Manages lifecycle of all smart robots as FastAPI background tasks
"""
import asyncio
import logging
from datetime import datetime, timezone
from .inventory_robot import InventoryRobot
from .debt_robot import DebtRobot
from .report_robot import ReportRobot

logger = logging.getLogger(__name__)


class RobotManager:
    def __init__(self, main_db, client):
        self.db = main_db
        self.client = client
        self.robots = {}
        self.tasks = {}
        self.started_at = None

    def initialize(self):
        self.robots = {
            "inventory": InventoryRobot(self.db, self.client),
            "debt": DebtRobot(self.db, self.client),
            "report": ReportRobot(self.db, self.client),
        }
        logger.info(f"Initialized {len(self.robots)} robots")

    async def start_all(self):
        if not self.robots:
            self.initialize()
        self.started_at = datetime.now(timezone.utc).isoformat()
        for name, robot in self.robots.items():
            task = asyncio.create_task(robot.start(), name=f"robot_{name}")
            self.tasks[name] = task
            logger.info(f"Started robot: {robot.name}")

    async def stop_all(self):
        for name, robot in self.robots.items():
            await robot.stop()
            if name in self.tasks:
                self.tasks[name].cancel()
        self.tasks.clear()
        logger.info("All robots stopped")

    async def restart_robot(self, name: str) -> bool:
        if name not in self.robots:
            return False
        robot = self.robots[name]
        await robot.stop()
        if name in self.tasks:
            self.tasks[name].cancel()
        await asyncio.sleep(1)
        task = asyncio.create_task(robot.start(), name=f"robot_{name}")
        self.tasks[name] = task
        logger.info(f"Restarted robot: {robot.name}")
        return True

    async def run_robot_once(self, name: str, **kwargs):
        if name not in self.robots:
            return None
        return await self.robots[name].run_once(**kwargs)

    def get_status(self) -> dict:
        status = {
            "started_at": self.started_at,
            "robots": {},
        }
        for name, robot in self.robots.items():
            status["robots"][name] = {
                "name": robot.name,
                "is_running": robot.is_running,
                "last_run": robot.last_run,
                "stats": robot.stats,
            }
        return status
