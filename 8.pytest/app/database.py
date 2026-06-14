from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import setting

engine = create_engine(setting.DATABASE_URL)
sessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()