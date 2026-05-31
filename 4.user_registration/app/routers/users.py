from fastapi import APIRouter, Depends, HTTPException
from app.database import sessionLocal
from sqlalchemy.orm import Session
from app.utils import hash_password
from app.schemas.users import UserCreate, UserResponse
from app.crud.users import get_user_by_email, create_user

router = APIRouter(prefix='/users', tags=['users'])

def get_db():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post('/register', response_model=UserResponse)
def registration(user: UserCreate, db: Session = Depends(get_db)):
    if get_user_by_email(user.email, db):
        raise HTTPException(status_code=400, detail="Email already registered")
    user.password = hash_password(user.password)
    new_user = create_user(user, db)
    return new_user