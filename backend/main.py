from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import logging
from pathlib import Path
import asyncio

from config import settings
from database import Database
from proxmox_client import ProxmoxClient
from claude_analyzer import ClaudeAnalyzer
from batch_processor import BatchProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Proxmox Batch Processor",
    description="Batch analyze and document your entire Proxmox infrastructure using Claude AI",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
db = Database()
proxmox_client = None
claude_analyzer = None
batch_processor = None

# Track running jobs
running_jobs = {}


class BatchJobRequest(BaseModel):
    """Request to start a new batch analysis job"""
    pass


class BatchJobResponse(BaseModel):
    """Response with batch job information"""
    job_id: int
    status: str
    message: str


@app.on_event("startup")
async def startup_event():
    """Initialize database and clients on startup"""
    global proxmox_client, claude_analyzer, batch_processor

    logger.info("Starting Proxmox Batch Processor")

    # Initialize database
    await db.init_db()
    logger.info("Database initialized")

    # Initialize Proxmox client
    try:
        proxmox_client = ProxmoxClient(
            host=settings.proxmox_host,
            user=settings.proxmox_user,
            password=settings.proxmox_password,
            token_name=settings.proxmox_token_name,
            token_value=settings.proxmox_token_value,
            verify_ssl=settings.proxmox_verify_ssl
        )
        logger.info(f"Connected to Proxmox at {settings.proxmox_host}")
    except Exception as e:
        logger.error(f"Failed to connect to Proxmox: {e}")
        raise

    # Initialize Claude analyzer
    try:
        claude_analyzer = ClaudeAnalyzer(
            api_key=settings.anthropic_api_key,
            model=settings.claude_model,
            max_tokens=settings.claude_max_tokens
        )
        logger.info("Claude analyzer initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Claude analyzer: {e}")
        raise

    # Initialize batch processor
    batch_processor = BatchProcessor(proxmox_client, claude_analyzer, db)
    logger.info("Batch processor initialized")

    # Create output directory
    Path(settings.output_dir).mkdir(exist_ok=True)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Proxmox Batch Processor",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "proxmox_connected": proxmox_client is not None,
        "claude_initialized": claude_analyzer is not None
    }


@app.get("/cluster/info")
async def get_cluster_info():
    """Get Proxmox cluster information"""
    try:
        cluster_info = proxmox_client.get_cluster_info()
        return cluster_info
    except Exception as e:
        logger.error(f"Error fetching cluster info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cluster/resources")
async def get_cluster_resources():
    """Get all VMs and LXCs in the cluster"""
    try:
        resources = proxmox_client.get_all_resources()
        return {
            "total": len(resources),
            "vms": len([r for r in resources if r["vm_type"] == "qemu"]),
            "lxcs": len([r for r in resources if r["vm_type"] == "lxc"]),
            "resources": resources
        }
    except Exception as e:
        logger.error(f"Error fetching resources: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def run_batch_job_background(job_id: int):
    """Background task to run batch analysis"""
    try:
        running_jobs[job_id] = "running"
        logger.info(f"Starting background batch job {job_id}")
        await batch_processor.run_full_analysis()
        running_jobs[job_id] = "completed"
        logger.info(f"Batch job {job_id} completed")
    except Exception as e:
        logger.error(f"Batch job {job_id} failed: {e}")
        running_jobs[job_id] = "failed"


@app.post("/batch/start", response_model=BatchJobResponse)
async def start_batch_job(background_tasks: BackgroundTasks):
    """Start a new batch analysis job"""
    try:
        # Get resource count
        resources = proxmox_client.get_all_resources()
        total_resources = len(resources)

        if total_resources == 0:
            raise HTTPException(status_code=400, detail="No resources found to analyze")

        # Create job in database
        job_id = await db.create_batch_job(total_resources)

        # Start background processing
        background_tasks.add_task(run_batch_job_background, job_id)

        return BatchJobResponse(
            job_id=job_id,
            status="started",
            message=f"Batch job {job_id} started. Analyzing {total_resources} resources."
        )

    except Exception as e:
        logger.error(f"Error starting batch job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/batch/jobs")
async def get_all_jobs():
    """Get all batch jobs"""
    try:
        jobs = await db.get_all_batch_jobs()
        return {"jobs": jobs}
    except Exception as e:
        logger.error(f"Error fetching jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/batch/jobs/{job_id}")
async def get_batch_job(job_id: int):
    """Get details for a specific batch job"""
    try:
        job = await db.get_batch_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # Get VM analyses
        analyses = await db.get_vm_analyses(job_id)

        # Get reports
        reports = await db.get_infrastructure_reports(job_id)

        return {
            "job": job,
            "analyses": analyses,
            "reports": reports
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/batch/jobs/{job_id}/status")
async def get_job_status(job_id: int):
    """Get status of a batch job"""
    try:
        job = await db.get_batch_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        return {
            "job_id": job_id,
            "status": job["status"],
            "progress": {
                "processed": job["processed_vms"],
                "total": job["total_vms"],
                "percentage": round((job["processed_vms"] / job["total_vms"]) * 100, 2) if job["total_vms"] > 0 else 0
            },
            "started_at": job["started_at"],
            "completed_at": job.get("completed_at"),
            "error_message": job.get("error_message")
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching job status for {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/batch/jobs/{job_id}/analyses/{vm_id}")
async def get_vm_analysis(job_id: int, vm_id: str):
    """Get analysis for a specific VM in a batch job"""
    try:
        analyses = await db.get_vm_analyses(job_id)
        vm_analysis = next((a for a in analyses if a["vm_id"] == vm_id), None)

        if not vm_analysis:
            raise HTTPException(status_code=404, detail="VM analysis not found")

        return vm_analysis
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching VM analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/batch/jobs/{job_id}/download")
async def download_job_outputs(job_id: int):
    """Download all outputs for a batch job as a zip file"""
    try:
        output_dir = Path(settings.output_dir) / f"job_{job_id}"

        if not output_dir.exists():
            raise HTTPException(status_code=404, detail="Job outputs not found")

        # Create zip file
        import shutil
        zip_path = Path(settings.output_dir) / f"job_{job_id}.zip"

        shutil.make_archive(
            str(zip_path.with_suffix('')),
            'zip',
            str(output_dir)
        )

        return FileResponse(
            path=str(zip_path),
            filename=f"proxmox_batch_job_{job_id}.zip",
            media_type="application/zip"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating download: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Mount frontend static files at root
frontend_path = Path(__file__).parent / "frontend"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=False
    )
