from fastapi import FastAPI
from app.routers.product import router as products_router
from app.models import product as models
from app.database import engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(products_router)