# Create a FastAPI app with a root route that returns your name and age as JSON.
# Add a GET route /items/{item_id} that takes an integer item_id and returns it back.
# Add a query parameter route /search that accepts a keyword string and returns it.

# from fastapi import FastAPI
# app=FastAPI()

# @app.get("/")
# def root():
#     return{
#         "name":"azhar",
#         "age":23
#     }

# @app.get("/items/{item_id}")
# def get_item(item_id:int):
#     return item_id

# @app.get("/search")
# def get_string(keyword:str):
#     return keyword

# ------------------------------------------------------------------------------------------------------------------

# Create a Pydantic model called Product with fields name (str), price (float), and in_stock (bool).
# Create a POST route /products/{product_id} that accepts a Product model and stores it in a dictionary. Return 201 on success and 400 if the product already exists.
# Create a GET route /products/{product_id} that fetches a product by ID and returns 404 if it doesn't exist. 

# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel

# app=FastAPI()

# class Product(BaseModel):
#     name:str
#     price:float
#     in_stock:bool

# products={}

# @app.post("/products/{product_id}", status_code=201)
# def create_product(product_id:int, product:Product):
#     if product_id in products:
#         raise HTTPException(status_code=400, detail="bad request")
#     products[product_id]= product.dict()
#     return products[product_id]

# @app.get("/products/{product_id}")
# def fetch_product(product_id:int):
#     if product_id not in products:
#         raise HTTPException(status_code=404, detail="file doesnt exist")
#     return products[product_id]

# ------------------------------------------------------------------------------------------------------------------
# Add a PUT route /products/{product_id} that updates only the fields that are provided. Use an UpdateProduct model with all optional fields.
# Add a DELETE route /products/{product_id} that removes the product and returns a confirmation message. Return 404 if it doesn't exist.
# Add a GET route /products that returns all products currently in the dictionary.

# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel
# from typing import Optional

# app=FastAPI()

# class Product(BaseModel):
#     name:str
#     price:float
#     in_stock:bool

# products={}

# @app.post("/products/{product_id}", status_code=201)
# def create_product(product_id:int, product:Product):
#     if product_id in products:
#         raise HTTPException(status_code=400, detail="bad request")
#     products[product_id]= product.dict()
#     return products[product_id]

# class UpdateProduct(BaseModel):
#     name:Optional[str] =None
#     price:Optional[float]=None
#     in_stock:Optional[bool]=None

# @app.put("/products/{product_id}")
# def update_product(product_id:int, product:UpdateProduct):
#     if product_id not in products:
#         raise HTTPException(status_code=404, detail="product not found")
#     if product.name is not None:
#         products[product_id]["name"]=product.name
#     if product.price is not None:
#         products[product_id]["price"]=product.price
#     if product.in_stock is not None:
#         products[product_id]["in_stock"]=product.in_stock
#     return products[product_id]

# @app.delete("/products/{product_id}")
# def remove_product(product_id:int):
#     if product_id not in products:
#         raise HTTPException(status_code=404, detail="file not found")
#     deleted_product=products.pop(product_id)
#     return{"message":"product deleted", "product": deleted_product}

# @app.get("/products")
# def list_products():
#     return products


