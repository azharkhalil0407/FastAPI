from sqlalchemy import Column, Integer, String, Boolean
from app.database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    price = Column(Integer)
    in_stock = Column(Boolean, default=True)