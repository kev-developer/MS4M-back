import asyncio
import json
from fastapi.responses import StreamingResponse
from src.services.simulation import SimulationEngine
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

# Pasamos una semilla (seed=42) para que las rutas iniciales sean predecibles en desarrollo
simulation_engine = SimulationEngine(graph_service=graph_service, seed=42)

@app.get("/tramos")
def get_tramos():
    return {
        "routes": graph_service.routes_data,
        "loads": graph_service.loads,
        "dumps": graph_service.dumps
    }

@app.post("/simulacion/iniciar")
async def start_simulation():
    await simulation_engine.start()
    return {"message": "Simulación iniciada"}

@app.post("/simulacion/detener")
def stop_simulation():
    simulation_engine.stop()
    return {"message": "Simulación detenida"}

@app.get("/simulacion/stream")
async def stream_simulation():
    """
    Mantiene una conexión HTTP abierta y emite el estado de la flota en tiempo real.
    """
    async def event_generator():
        while True:
            if not simulation_engine.is_running:
                await asyncio.sleep(1)
                continue

            trucks_data = [
                {
                    "id": truck.truck_id,
                    "status": truck.status,
                    "lat": truck.current_pos[0],
                    "lng": truck.current_pos[1],
                    "speed": round(truck.current_speed, 2)
                }
                for truck in simulation_engine.trucks
            ]
            
            # SSE requiere este formato: "data: <string_json>\n\n"
            payload = json.dumps(trucks_data)
            yield f"data: {payload}\n\n"
            
            await asyncio.sleep(simulation_engine.update_interval)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
