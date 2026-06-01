from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.utils import hash_password, verify_password,create_access_token, get_current_user
from app.schemas.users import UserCreate, UserResponse
from app.crud.users import get_user_by_email, create_user
from app.dependencies import get_db
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(prefix='/users', tags=['users'])

@router.post('/register', response_model=UserResponse)
def registration(user: UserCreate, db: Session = Depends(get_db)):
    if get_user_by_email(user.email, db):
        raise HTTPException(status_code=400, detail="Email already registered")
    user.password = hash_password(user.password)
    new_user = create_user(user, db)
    return new_user

@router.post('/login')
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = get_user_by_email(form_data.username,db)
    if not user:
        raise HTTPException(status_code=401)
    flag=verify_password(form_data.password, user.password)
    if not flag:
        raise HTTPException(status_code=401)
    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}

@router.get('/me', response_model=UserResponse)
def get_me(current_user = Depends(get_current_user)):
    return current_user
