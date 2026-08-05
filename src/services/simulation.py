import asyncio
import random
import time
from datetime import datetime
from typing import List, Tuple, Optional
from .graph_service import haversine_distance
from .routing_service import RoutingService

class Truck:
    def __init__(self, truck_id: str):
        self.truck_id = truck_id
        self.status = "IDLE"
        self.route: List[Tuple[float, float]] = []
        self.route_index = 0
        self.current_pos: Tuple[float, float] = (0.0, 0.0)
        self.current_speed = 0.0
        self.history = []
        self.error_reason: Optional[str] = None

    def assign_route(self, route: List[Tuple[float, float]]):
        self.route = route
        self.route_index = 0
        self.current_pos = route[0]
        self.status = "MOVING"
        self.history = []
        self.error_reason = None

    def mark_error(self, reason: str):
        self.status = "ERROR"
        self.error_reason = reason

class SimulationEngine:
    def __init__(self, graph_service, seed: Optional[int] = None,
                 speed_min: float = 40.0, speed_max: float = 80.0,
                 time_multiplier: float = 5.0):
        if seed is not None:
            random.seed(seed)

        self.graph_service = graph_service
        self.trucks = [Truck(f"CAM-{i:03d}") for i in range(1, 6)]

        self.is_running = False
        self.update_interval = 0.1
        self.time_multiplier = time_multiplier
        self.speed_min = speed_min
        self.speed_max = speed_max
        self._last_time: Optional[float] = None

    def _assign_random_routes(self):
        loads = self.graph_service.loads
        dumps = self.graph_service.dumps
        graph = self.graph_service.get_graph()

        for truck in self.trucks:
            valid_route = None
            last_load = None
            last_dump = None
            attempts = 0

            while not valid_route and attempts < 100:
                last_load = random.choice(loads)
                last_dump = random.choice(dumps)
                valid_route = RoutingService.calculate_route(
                    graph, last_load['coor'], last_dump['coor']
                )
                attempts += 1

            if valid_route:
                truck.assign_route(valid_route)
            else:
                reason = f"No hay ruta conectada entre '{last_load['name']}' y '{last_dump['name']}' después de 100 intentos"
                truck.mark_error(reason)

    async def start(self):
        if self.is_running:
            return
            
        self._assign_random_routes()
        self.is_running = True
        asyncio.create_task(self._simulation_loop())

    def stop(self):
        self.is_running = False

    def set_time_multiplier(self, value: float):
        """Cambia time_multiplier y reinicia el reloj de simulación para evitar saltos."""
        if value <= 0:
            raise ValueError("time_multiplier debe ser > 0")
        self.time_multiplier = value
        # Reiniciar el reloj para evitar que el siguiente dt sea enorme
        if self.is_running:
            self._last_time = time.time()

    async def _simulation_loop(self):
        self._last_time = time.time()

        while self.is_running:
            current_time = time.time()

            dt = (current_time - self._last_time) * self.time_multiplier
            self._last_time = current_time

            for truck in self.trucks:
                if truck.status == "MOVING":
                    self._update_truck(truck, dt)

            await asyncio.sleep(self.update_interval)

    def _update_truck(self, truck: Truck, dt: float):
        speed_kmh = random.uniform(self.speed_min, self.speed_max)
        truck.current_speed = speed_kmh
        
        truck.history.append({
            "timestamp": datetime.now().isoformat(),
            "speed": speed_kmh
        })

        speed_ms = speed_kmh * (1000 / 3600)
        distance_to_move = speed_ms * dt

        while distance_to_move > 0 and truck.route_index < len(truck.route) - 1:
            current_point = truck.current_pos
            next_point = truck.route[truck.route_index + 1]
            
            dist_to_next = haversine_distance(list(current_point), list(next_point))
            
            if distance_to_move >= dist_to_next:
                # El camión supera el punto actual, avanzamos al siguiente segmento
                distance_to_move -= dist_to_next
                truck.route_index += 1
                truck.current_pos = next_point
            else:
                # El camión se queda a medio camino: Interpolación lineal
                fraction = distance_to_move / dist_to_next
                lat = current_point[0] + (next_point[0] - current_point[0]) * fraction
                lon = current_point[1] + (next_point[1] - current_point[1]) * fraction
                
                truck.current_pos = (lat, lon)
                distance_to_move = 0 # Terminó su movimiento en este tick

        if truck.route_index >= len(truck.route) - 1:
            truck.status = "FINISHED"
            truck.current_speed = 0.0