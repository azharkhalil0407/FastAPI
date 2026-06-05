from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()


# Basic Routes
@app.get("/")
def root():
    return {
        "name": "Azhar",
        "age": 23
    }


@app.get("/items/{item_id}")
def get_item(item_id: int):
    return {"item_id": item_id}


@app.get("/search")
def search(keyword: str):
    return {"keyword": keyword}


# Pydantic Models
class Product(BaseModel):
    name: str
    price: float
    in_stock: bool


class UpdateProduct(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    in_stock: Optional[bool] = None


# In-Memory Database
products = {}



# Product Routes
@app.post("/products/{product_id}", status_code=201)
def create_product(product_id: int, product: Product):
    if product_id in products:
        raise HTTPException(
            status_code=400,
            detail="Product already exists"
        )

    products[product_id] = product.dict()
    return products[product_id]


@app.get("/products")
def list_products():
    return products


@app.get("/products/{product_id}")
def get_product(product_id: int):
    if product_id not in products:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    return products[product_id]


@app.put("/products/{product_id}")
def update_product(product_id: int, product: UpdateProduct):
    if product_id not in products:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    update_data = product.dict(exclude_unset=True)

    for key, value in update_data.items():
        products[product_id][key] = value

    return products[product_id]


@app.delete("/products/{product_id}")
def delete_product(product_id: int):
    if product_id not in products:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    deleted_product = products.pop(product_id)

    return {
        "message": "Product deleted successfully",
        "product": deleted_product
    }
