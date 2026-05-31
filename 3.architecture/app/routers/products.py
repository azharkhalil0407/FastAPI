from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import sessionLocal
from app.schemas.products import ProductCreate, ProductUpdate, ProductResponse
from app.crud.products import get_all_products, get_product_by_id, create_product, update_product, delete_product

router = APIRouter(prefix='/products', tags=['products'])

def get_db():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get('/', response_model=list[ProductResponse])
def list_products(db: Session = Depends(get_db)):
    return get_all_products(db)

@router.get('/{product_id}', response_model=ProductResponse)
def fetch_product(product_id: int, db: Session = Depends(get_db)):
    product = get_product_by_id(product_id, db)
    if product is None:
        raise HTTPException(status_code=404, detail='Product not found')
    return product

@router.post('/', status_code=201, response_model=ProductResponse)
def add_product(product: ProductCreate, db: Session = Depends(get_db)):
    return create_product(product, db)

@router.put('/{product_id}', response_model=ProductResponse)
def edit_product(product_id: int, product: ProductUpdate, db: Session = Depends(get_db)):
    existing = get_product_by_id(product_id, db)
    if existing is None:
        raise HTTPException(status_code=404, detail='Product not found')
    return update_product(product_id, product, db)

@router.delete('/{product_id}')
def remove_product(product_id: int, db: Session = Depends(get_db)):
    existing = get_product_by_id(product_id, db)
    if existing is None:
        raise HTTPException(status_code=404, detail='Product not found')
    delete_product(product_id, db)
    return {"message": "Product deleted"}