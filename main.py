from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from services.graph_service import GraphService

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


# Cargamos el grafo en memoria al arrancar la app
graph_service = GraphService(json_path="../data/datos_prueba.json")

@app.get("/tramos")
def get_tramos():
    # Retornamos los datos para que el Frontend dibuje el mapa
    return graph_service.routes_data


