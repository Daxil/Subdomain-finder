import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import Target, ScanJob

db = SessionLocal()
print("Start to clear DB...")


db.query(ScanJob).delete()

db.query(Target).delete()

db.commit()
print("DB clear!")
db.close()
