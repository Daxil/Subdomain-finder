import sys
import argparse
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import Target, ScanJob, ScanStatus
from app.tasks.recon import run_subdomain_scan

def main():
    parser = argparse.ArgumentParser(description="Automate search subdommain")
    parser.add_argument("domain", help="Domain for scan... (example: vk.com)")
    args = parser.parse_args()
    
    domain = args.domain
    db = SessionLocal()
    print(f"\nTarget: {domain}")
    print("Task in queue (Redis) and wait worker...\n")
    
  
    target = db.query(Target).filter(Target.domain == domain).first()
    is_new_target = False
    
    if not target:
        target = Target(domain=domain)
        db.add(target)
        db.commit()
        db.refresh(target)
        is_new_target = True
    
    job = ScanJob(target_id=target.id, status=ScanStatus.pending)
    db.add(job)
    db.commit()
    db.refresh(job) 
    
    async_result = run_subdomain_scan.delay(job.id, domain)
    
    try:
        result_data = async_result.get(timeout=120)
    except Exception as e:
        print(f"x Error waiting for task: {e}")
        # Чистим за собой, если упали с ошибкой
        db.delete(job)
        if is_new_target:
            db.delete(target)
        db.commit()
        db.close()
        return
        
    if isinstance(result_data, list):
        print(f"Success! Found subdomain : {len(result_data)}\n")
        print("=" * 50)
        for sub in sorted(result_data):
            print(f"{sub}")
        print("=" * 50)
    elif isinstance(result_data, dict) and 'error' in result_data:
        print(f"x Error scan:  {result_data['error']}")
    else:
        print(f"Unexpected result:{result_data}")

    db.delete(job)

    if is_new_target:
        db.delete(target)
    db.commit()
    print(f"DB cleared")
    
    db.close()  
    
if __name__ == "__main__":
    main()
