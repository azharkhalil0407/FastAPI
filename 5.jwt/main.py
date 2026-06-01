from fastapi import FastAPI
from app.models.users import User
from app.database import Base, engine
from app.routers.users import router as user_router

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(user_router)