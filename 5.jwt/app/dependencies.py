from app.database import sessionLocal
from sqlalchemy.orm import Session

def get_db():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()