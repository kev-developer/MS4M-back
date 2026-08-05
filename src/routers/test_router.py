from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.get("/")
def test():
    return {"test":"asd"}