from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.crud import product as crud

router = APIRouter(
    prefix="/products",
    tags=["products"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/")
def list_products(db: Session = Depends(get_db)):
    return crud.get_all_products(db)

@router.get("/{product_id}")
def fetch_product(product_id: int, db: Session = Depends(get_db)):
    product = crud.get_product_by_id(db, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="product not found")
    return product

@router.post("/", status_code=201)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    return crud.create_product(db, product)

@router.put("/{product_id}")
def update_product(product_id: int, product: ProductUpdate, db: Session = Depends(get_db)):
    existing = crud.get_product_by_id(db, product_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="product not found")
    return crud.update_product(db, product_id, product)

@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    existing = crud.get_product_by_id(db, product_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="product not found")
    db.close()
    return crud.delete_product(db, product_id)