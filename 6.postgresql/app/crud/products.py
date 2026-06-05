from sqlalchemy.orm import Session

from app.models.products import Product
from app.schemas.products import ProductCreate, ProductUpdate

def get_all_products(db: Session):
    return db.query(Product).all()

def get_product_by_id(product_id: int, db: Session):
    return db.query(Product).filter(Product.id == product_id).first()

def create_product(product: ProductCreate, db: Session):
    new_product = Product(name=product.name, price=product.price, in_stock=product.in_stock, user_id=product.user_id)
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

def update_product(product_id: int, product: ProductUpdate, db: Session):
    existing = get_product_by_id(product_id, db)
    
    if product.name is not None:
        existing.name = product.name
    
    if product.price is not None:
        existing.price = product.price
    
    if product.in_stock is not None:
        existing.in_stock = product.in_stock
    
    db.commit()
    db.refresh(existing)
    
    return existing

def delete_product(product_id: int, db: Session):
    existing = get_product_by_id(product_id, db)
    db.delete(existing)
    db.commit()