import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, Base
from app.models import Target, ScanJob

def init():
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully.")

if __name__ == "__main__":
    init()
