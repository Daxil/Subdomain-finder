import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import ScanJob, Target

db = SessionLocal()
jobs = db.query(ScanJob).order_by(ScanJob.id.desc()).limit(3).all()

print("\n=== ПОСЛЕДНИЕ ЗАДАЧИ СКАНИРОВАНИЯ ===")
for job in jobs:
    target = db.query(Target).filter(Target.id == job.target_id).first()
    print(f"\n🔹 Job ID: {job.id} | Домен: {target.domain if target else 'Unknown'}")
    print(f"   Статус: {job.status}")


    if job.results:
        if 'error' in job.results:
            print(f"   ❌ Ошибка: {job.results['error']}")
        else:
            count = job.results.get('count', 0)
            print(f"   🎯 Найдено поддоменов: {count}")
            if count > 0:

                subdomains = job.results.get('subdomains', [])
                print(f"   Примеры: {subdomains[:5]}")
    print("-" * 40)

db.close()
