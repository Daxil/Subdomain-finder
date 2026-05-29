import subprocess
import json
from datetime import datetime, timezone
from app.celery_app import celery_app
from app.database import SessionLocal
from app.models import ScanJob, ScanStatus

@celery_app.task(bind=True, name="app.tasks.recon.run_subdomain_scan")
def run_subdomain_scan(self, job_id: int, domain: str):
    db = SessionLocal()
    job = None
    try:
        job = db.query(ScanJob).filter(ScanJob.id == job_id).first()
        if not job:
            return f"Job {job_id} not found"


        job.status = ScanStatus.running
        db.commit()


        cmd = ["subfinder", "-d", domain, "-silent", "-json"]

        try:

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        except FileNotFoundError:
            job.status = ScanStatus.failed
            job.results = {"error": "subfinder не найден в системе."}
            job.finished_at = datetime.now(timezone.utc)
            db.commit()
            return "subfinder not found"

        subdomains = []
        if result.returncode == 0 and result.stdout:

            for line in result.stdout.strip().split('\n'):
                if line:
                    try:
                        data = json.loads(line)
                        subdomains.append(data.get("host", line))
                    except json.JSONDecodeError:
                        subdomains.append(line)
        else:
            subdomains = []


        subdomains = list(set(subdomains))

        job.status = ScanStatus.completed
        job.results = {"subdomains": subdomains, "count": len(subdomains)}
        job.finished_at = datetime.now(timezone.utc)
        db.commit()

        return subdomains

    except Exception as e:

        if job:
            job.status = ScanStatus.failed
            job.results = {"error": str(e)}
            job.finished_at = datetime.now(timezone.utc)
            db.commit()
        return {"error": str(e)}
    finally:
        db.close()
