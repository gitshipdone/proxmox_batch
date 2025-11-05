import aiosqlite
import json
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path


class Database:
    def __init__(self, db_path: str = "proxmox_batch.db"):
        self.db_path = db_path

    async def init_db(self):
        """Initialize database with required tables"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS batch_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    status TEXT,
                    total_vms INTEGER,
                    processed_vms INTEGER,
                    error_message TEXT
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS vm_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    batch_job_id INTEGER,
                    vm_id TEXT,
                    vm_name TEXT,
                    vm_type TEXT,
                    node TEXT,
                    config JSON,
                    analysis TEXT,
                    security_review TEXT,
                    optimization_recommendations TEXT,
                    terraform_template TEXT,
                    ansible_playbook TEXT,
                    analyzed_at TIMESTAMP,
                    FOREIGN KEY (batch_job_id) REFERENCES batch_jobs (id)
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS infrastructure_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    batch_job_id INTEGER,
                    report_type TEXT,
                    content TEXT,
                    created_at TIMESTAMP,
                    FOREIGN KEY (batch_job_id) REFERENCES batch_jobs (id)
                )
            """)

            await db.commit()

    async def create_batch_job(self, total_vms: int) -> int:
        """Create a new batch job and return its ID"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "INSERT INTO batch_jobs (started_at, status, total_vms, processed_vms) VALUES (?, ?, ?, ?)",
                (datetime.now().isoformat(), "running", total_vms, 0)
            )
            await db.commit()
            return cursor.lastrowid

    async def update_batch_job(self, job_id: int, processed: int, status: str = "running", error: str = None):
        """Update batch job progress"""
        async with aiosqlite.connect(self.db_path) as db:
            if status == "completed":
                await db.execute(
                    "UPDATE batch_jobs SET processed_vms = ?, status = ?, completed_at = ? WHERE id = ?",
                    (processed, status, datetime.now().isoformat(), job_id)
                )
            else:
                await db.execute(
                    "UPDATE batch_jobs SET processed_vms = ?, status = ?, error_message = ? WHERE id = ?",
                    (processed, status, error, job_id)
                )
            await db.commit()

    async def save_vm_analysis(self, batch_job_id: int, vm_data: Dict):
        """Save VM analysis results"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO vm_analysis (
                    batch_job_id, vm_id, vm_name, vm_type, node, config,
                    analysis, security_review, optimization_recommendations,
                    terraform_template, ansible_playbook, analyzed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                batch_job_id,
                vm_data["vm_id"],
                vm_data["vm_name"],
                vm_data["vm_type"],
                vm_data["node"],
                json.dumps(vm_data["config"]),
                vm_data.get("analysis"),
                vm_data.get("security_review"),
                vm_data.get("optimization_recommendations"),
                vm_data.get("terraform_template"),
                vm_data.get("ansible_playbook"),
                datetime.now().isoformat()
            ))
            await db.commit()

    async def save_infrastructure_report(self, batch_job_id: int, report_type: str, content: str):
        """Save infrastructure report"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO infrastructure_reports (batch_job_id, report_type, content, created_at)
                VALUES (?, ?, ?, ?)
            """, (batch_job_id, report_type, content, datetime.now().isoformat()))
            await db.commit()

    async def get_batch_job(self, job_id: int) -> Optional[Dict]:
        """Get batch job details"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM batch_jobs WHERE id = ?", (job_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
                return None

    async def get_all_batch_jobs(self) -> List[Dict]:
        """Get all batch jobs"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM batch_jobs ORDER BY started_at DESC") as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_vm_analyses(self, batch_job_id: int) -> List[Dict]:
        """Get all VM analyses for a batch job"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM vm_analysis WHERE batch_job_id = ?",
                (batch_job_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_infrastructure_reports(self, batch_job_id: int) -> List[Dict]:
        """Get all infrastructure reports for a batch job"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM infrastructure_reports WHERE batch_job_id = ?",
                (batch_job_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
