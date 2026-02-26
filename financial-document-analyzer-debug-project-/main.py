"""
Financial Document Analyzer API.
- Sync: POST /analyze/sync (blocking, returns result in response).
- Async: POST /analyze (enqueue job, returns job_id); GET /analyze/{job_id} (poll result).
"""
import asyncio
import os
import uuid
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config import UPLOAD_DIR, DATA_DIR
from database import init_db, get_db, AnalysisJob, JobStatus
from celery_tasks import run_analysis_task

app = FastAPI(
    title="Financial Document Analyzer API",
    description="Upload financial PDFs and get AI-powered analysis. Supports sync and queue-based async processing.",
    version="1.0.0",
)


def run_crew(query: str, file_path: str) -> str:
    """Run the crew synchronously (used by sync endpoint and by Celery worker)."""
    from crewai import Crew, Process
    from agents import financial_analyst
    from task import analyze_financial_document

    crew = Crew(
        agents=[financial_analyst],
        tasks=[analyze_financial_document],
        process=Process.sequential,
    )
    inputs = {"query": query, "file_path": file_path}
    result = crew.kickoff(inputs)
    return str(result)


# Ensure dirs and DB on startup
@app.on_event("startup")
def startup():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    init_db()


@app.get("/")
async def root():
    """Health check."""
    return {"message": "Financial Document Analyzer API is running", "docs": "/docs"}


# ---------- Sync endpoint (blocking) ----------
@app.post("/analyze/sync")
async def analyze_sync(
    file: UploadFile = File(...),
    query: str = Form(default="Analyze this financial document for investment insights"),
    db: Session = Depends(get_db),
):
    """
    Analyze a financial document and return the result in the response (blocking).
    Use for small files and when you can wait for the result.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="A PDF file is required.")

    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"financial_document_{file_id}.pdf")

    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    query = (query or "").strip() or "Analyze this financial document for investment insights"

    try:
        # Run crew in thread pool to avoid blocking the event loop
        response = await asyncio.to_thread(run_crew, query=query, file_path=file_path)
        return {
            "status": "success",
            "query": query,
            "analysis": response,
            "file_processed": file.filename,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")
    finally:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass


# ---------- Async (queue) endpoints ----------
class AnalyzeResponse(BaseModel):
    job_id: str
    status: str
    message: str


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_async(
    file: UploadFile = File(...),
    query: str = Form(default="Analyze this financial document for investment insights"),
    db: Session = Depends(get_db),
):
    """
    Enqueue a financial document for analysis. Returns immediately with a job_id.
    Poll GET /analyze/{job_id} for status and result.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="A PDF file is required.")

    job_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"financial_document_{job_id}.pdf")

    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    query = (query or "").strip() or "Analyze this financial document for investment insights"

    job = AnalysisJob(
        id=job_id,
        status=JobStatus.PENDING,
        file_path=file_path,
        original_filename=file.filename,
        query=query,
    )
    db.add(job)
    db.commit()

    # Enqueue Celery task (fire-and-forget)
    try:
        run_analysis_task.delay(
            job_id=job_id,
            file_path=file_path,
            query=query,
            original_filename=file.filename,
        )
    except Exception as e:
        job.status = JobStatus.FAILED
        job.error_message = f"Failed to enqueue: {e}"
        db.commit()
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass
        raise HTTPException(status_code=503, detail="Queue unavailable; try /analyze/sync")

    return AnalyzeResponse(
        job_id=job_id,
        status=JobStatus.PENDING,
        message="Analysis queued. Poll GET /analyze/{job_id} for result.",
    )


@app.get("/analyze/{job_id}")
async def get_analysis_result(job_id: str, db: Session = Depends(get_db)):
    """Get status and result of an analysis job."""
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    out = {
        "job_id": job.id,
        "status": job.status,
        "query": job.query,
        "file_processed": job.original_filename,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None,
    }
    if job.status == JobStatus.COMPLETED:
        out["analysis"] = job.result_text
    if job.status == JobStatus.FAILED and job.error_message:
        out["error"] = job.error_message
    return out


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
