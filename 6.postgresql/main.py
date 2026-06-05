from fastapi import FastAPI

from app.database import Base, engine
from app.models.products import Product
from app.models.users import User
from app.routers.products import router as products_router
from app.routers.users import router as user_router

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(user_router)
app.include_router(products_router)