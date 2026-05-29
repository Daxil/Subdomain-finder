import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import Target, ScanJob, ScanStatus
from app.tasks.recon import run_subdomain_scan

def main():
    domain = "hackerone.com"

    db = SessionLocal()

    target= db.query(Target).filter(Target.domain == domain).first()
    if not target:
        target = Target(domain=domain)
        db.add(target)
        db.commit()
        db.refresh(target)

    job = ScanJob(target_id=target.id, status= ScanStatus.pending)
    db.add(job)
    db.commit()
    db.refresh(job)

    print(f"Create Job ID: {job.id} for domain: {domain}")

    run_subdomain_scan.delay(job.id, domain)
    print("Task send to queue (Redis).")

    db.close()

if __name__ == "__main__":
    main()
