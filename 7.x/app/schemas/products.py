from typing import Optional
from app.schemas.users import UserResponse
from pydantic import BaseModel,Field


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100,pattern=r"^[a-zA-Z ]+$")
    price: float = Field(..., gt=0)
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
    owner: UserResponse
    user_id:int

    class Config:
        from_attributes = True