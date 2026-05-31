from fastapi import FastAPI
from app.models.products import Product
from app.database import Base, engine
from app.routers.products import router as products_router

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(products_router)