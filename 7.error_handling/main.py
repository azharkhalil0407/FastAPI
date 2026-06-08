from fastapi import FastAPI, HTTPException

from app.database import Base, engine
from app.models.products import Product
from app.models.users import User
from app.routers.products import router as products_router
from app.routers.users import router as user_router

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi import Request

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(user_router)
app.include_router(products_router)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"status": "error", "message": "Invalid input"}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "message": exc.detail}
)