from sqlalchemy.orm import Session
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate

def get_all_products(db: Session):
    return db.query(Product).all()

def get_product_by_id(db: Session, product_id: int):
    return db.query(Product).filter(Product.id == product_id).first()

def create_product(db: Session, product: ProductCreate):
    new_product = Product(**product.dict())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

def update_product(db: Session, product_id: int, product: ProductUpdate):
    existing = get_product_by_id(db, product_id)
    if product.name is not None:
        existing.name = product.name
    if product.price is not None:
        existing.price = product.price
    if product.in_stock is not None:
        existing.in_stock = product.in_stock
    db.commit()
    db.refresh(existing)
    return existing

def delete_product(db: Session, product_id: int):
    existing = get_product_by_id(db, product_id)
    db.delete(existing)
    db.commit()