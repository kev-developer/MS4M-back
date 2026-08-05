from fastapi import APIRouter
from src.routers import test_router
from src.routers import item_router

api_router = APIRouter()

api_router.include_router(test_router.router, prefix="/test", tags=["Test"])
api_router.include_router(item_router.router, prefix="/items", tags=["Item"])