# Import FastAPI, SQLAlchemy session, Pydantic, and project modules
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

import day2_models
from day2_database import engine, SessionLocal
from day2_models import Product

# Create database tables using: Base.metadata.create_all(bind=engine)
day2_models.Base.metadata.create_all(bind=engine)

# Initialize FastAPI app instance
app=FastAPI()

# Define ProductSchema (request body for CREATE)
class ProductSchema(BaseModel):
    name:str
    price:float
    in_stock:bool

# Define UpdateProductSchema (request body for UPDATE with optional fields)
class UpdateProductSchema(BaseModel):
    name:Optional[str] = None
    price:Optional[float] = None
    in_stock:Optional[bool] = None

# Create get_db() function:
# open DB session
# yield session
# close session after request
def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create GET /products route:
# get DB via Depends
# fetch all products
# return list
@app.get("/products")
def list_products(db: Session=Depends(get_db)):
    product= db.query(Product).all()
    return product


# Create GET /products/{product_id} route:
# get DB via Depends
# query product by ID
# if not found → raise 404
# return product
@app.get("/products/{product_id}")
def fetch_product(product_id:int, db: Session=Depends(get_db)):
    product= db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="product not found")
    return product

# Create POST /products route:
# get request body
# convert schema → Product model
# add to DB
# commit
# refresh
# return new product
@app.post("/products", status_code=201)
def create_product(product:ProductSchema, db:Session=Depends(get_db)):
    new_product = Product(**product.dict())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product


# Create PUT /products/{product_id} route:
# fetch existing product
# if not found → 404
# update only provided fields
# commit
# refresh
# return updated product
@app.put("/products/{product_id}")
def update_product(product_id:int, product:UpdateProductSchema, db:Session=Depends(get_db)):
    existing= db.query(Product).filter(Product.id == product_id).first()
    if existing is None:
        raise HTTPException(status_code=404, detail="product not found")
    if product.name is not None:
        existing.name=product.name
    if product.price is not None:
        existing.price=product.price
    if product.in_stock is not None:
        existing.in_stock=product.in_stock
    db.commit()
    db.refresh(existing)
    return existing

# Create DELETE /products/{product_id} route:
# fetch product
# if not found → 404
# delete from DB
# commit
# return success message
@app.delete("/products/{product_id}")
def delete_product(product_id:int, db:Session=Depends(get_db)):
    existing=db.query(Product).filter(Product.id == product_id).first()
    if existing is None:
        raise HTTPException(status_code=404, detail="product not found")
    db.delete(existing)
    db.commit()
    return{"message": "product deleted"}