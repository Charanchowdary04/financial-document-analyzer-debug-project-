"""Celery tasks: run crew in worker and persist result to DB."""
import os
from celery_app import celery_app
from crewai import Crew, Process
from agents import financial_analyst
from task import analyze_financial_document
from database import SessionLocal, AnalysisJob, JobStatus

app = celery_app


def _run_crew_sync(query: str, file_path: str):
    """Synchronous crew execution (run inside worker)."""
    crew = Crew(
        agents=[financial_analyst],
        tasks=[analyze_financial_document],
        process=Process.sequential,
    )
    inputs = {"query": query, "file_path": file_path}
    result = crew.kickoff(inputs)
    return str(result)


@app.task(bind=True, name="financial_analyzer.run_analysis")
def run_analysis_task(self, job_id: str, file_path: str, query: str, original_filename: str = None):
    """Run analysis in worker and save result to database."""
    db = SessionLocal()
    try:
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        if not job:
            return {"ok": False, "error": "Job not found"}

        job.status = JobStatus.PROCESSING
        db.commit()

        if not os.path.isfile(file_path):
            job.status = JobStatus.FAILED
            job.error_message = f"File not found: {file_path}"
            db.commit()
            return {"ok": False, "error": job.error_message}

        try:
            result = _run_crew_sync(query=query, file_path=file_path)
            job.status = JobStatus.COMPLETED
            job.result_text = result
            job.error_message = None
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
        db.commit()
        return {"ok": job.status == JobStatus.COMPLETED, "job_id": job_id}
    finally:
        db.close()
        # Clean up file after processing
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass
