from fastapi import APIRouter
from src.schemas.item import Item
from src.local.bd import items

router = APIRouter()

@router.get("/")
def getAll():
    return {"test":items}

@router.post("/")
def add(item: Item):
    items.append(item)
    return {"Status":"Added"}

@router.delete("/{name}")
def delete(name: str):
    global items

    tmp_list = []
    for obj in items:
        if obj.name != name:
            tmp_list.append(obj)
    items = tmp_list

    return {"Status":"Deleted"}