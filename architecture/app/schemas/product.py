from pydantic import BaseModel
from typing import Optional

class ProductCreate(BaseModel):
    name: str
    price: float
    in_stock: bool

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    in_stock: Optional[bool] = None

class ProductResponse(BaseModel):
    id: int
    name: str
    price: float
    in_stock: bool

    class Config:
        from_attributes = True