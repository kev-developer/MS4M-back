import asyncio
import json
from fastapi.responses import StreamingResponse
from src.services.simulation import SimulationEngine
from src.services.report_service import ReportService
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from src.services.graph_service import GraphService
from pathlib import Path

origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "https://MS4M-front.vercel.app",
    "https://ms-4-m-front.vercel.app"
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

try:
    graph_service = GraphService(json_path=str(JSON_PATH))
except (FileNotFoundError, ValueError) as e:
    print(f"Error al cargar datos: {e}")
    exit(1)

# Configuración de simulación: speed_min/max en km/h, time_multiplier es aceleración (5.0x = 5 veces más rápido)
simulation_engine = SimulationEngine(
    graph_service=graph_service,
    seed=42,
    speed_min=40.0,
    speed_max=80.0,
    time_multiplier=5.0
)

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
                    "speed": round(truck.current_speed, 2),
                    "error_reason": truck.error_reason
                }
                for truck in simulation_engine.trucks
            ]
            
            # SSE requiere este formato: "data: <string_json>\n\n"
            payload = json.dumps(trucks_data)
            yield f"data: {payload}\n\n"
            
            await asyncio.sleep(simulation_engine.update_interval)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/reporte")
def get_report():
    report = ReportService.generate_report(simulation_engine.trucks)
    return report

@app.post("/simulacion/config")
def update_config(
    time_multiplier: float | None = None,
    speed_min: float | None = None,
    speed_max: float | None = None
):
    """Actualiza parámetros de simulación en tiempo de ejecución.

    - time_multiplier: aceleración de tiempo (ej. 5.0 = 5x más rápido)
    - speed_min: velocidad mínima en km/h
    - speed_max: velocidad máxima en km/h
    """
    changes = {}

    if time_multiplier is not None:
        try:
            simulation_engine.set_time_multiplier(time_multiplier)
            changes["time_multiplier"] = time_multiplier
        except ValueError as e:
            return {"error": str(e)}

    if speed_min is not None:
        if speed_min <= 0:
            return {"error": "speed_min debe ser > 0"}
        simulation_engine.speed_min = speed_min
        changes["speed_min"] = speed_min

    if speed_max is not None:
        if speed_max <= 0:
            return {"error": "speed_max debe ser > 0"}
        simulation_engine.speed_max = speed_max
        changes["speed_max"] = speed_max

    if not changes:
        return {"message": "Sin cambios", "current": {
            "time_multiplier": simulation_engine.time_multiplier,
            "speed_min": simulation_engine.speed_min,
            "speed_max": simulation_engine.speed_max
        }}

    return {"message": "Configuración actualizada", "changes": changes}