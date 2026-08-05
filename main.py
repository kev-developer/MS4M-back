from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from src.services.graph_service import GraphService
from pathlib import Path

origins = [
    "http://localhost:5173",
    "https://est-react.vercel.app"
    ]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins = origins,
    allow_methods = ["*"],
    allow_headers = ["*"],
    )

BASE_DIR = Path(__file__).resolve().parent

JSON_PATH = BASE_DIR / "data" / "data-prueba.json"
graph_service = GraphService(json_path=str(JSON_PATH))

@app.get("/tramos")
def get_tramos():
    return graph_service.routes_data


