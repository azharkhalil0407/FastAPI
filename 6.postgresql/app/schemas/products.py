from typing import Optional

from pydantic import BaseModel


class ProductCreate(BaseModel):
    name: str
    price: float
    in_stock: bool

    user_id:int


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    in_stock: Optional[bool] = None


class ProductResponse(BaseModel):
    id: int
    name: str
    price: float
    in_stock: bool

    user_id:int

    class Config:
        from_attributes = True