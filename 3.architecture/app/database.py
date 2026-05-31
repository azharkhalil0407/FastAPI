from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import setting

engine=create_engine(setting.DATABASE_URL, connect_args={"check_same_thread":False})
sessionLocal=sessionmaker(autoflush=False, autocommit=False, bind=engine)
Base=declarative_base()