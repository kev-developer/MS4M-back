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
        self.status = "IDLE" # Estados: IDLE, MOVING, FINISHED, ERROR
        self.route: List[Tuple[float, float]] = []
        self.route_index = 0
        self.current_pos: Tuple[float, float] = (0.0, 0.0)
        self.current_speed = 0.0
        self.history = []

    def assign_route(self, route: List[Tuple[float, float]]):
        self.route = route
        self.route_index = 0
        self.current_pos = route[0]
        self.status = "MOVING"
        self.history = []

class SimulationEngine:
    def __init__(self, graph_service, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)
            
        self.graph_service = graph_service
        self.trucks = [Truck(f"CAM-{i:03d}") for i in range(1, 6)]
        
        self.is_running = False
        self.update_interval = 0.1
        self.time_multiplier = 5.0

    def _assign_random_routes(self):
        loads = self.graph_service.loads
        dumps = self.graph_service.dumps
        graph = self.graph_service.get_graph()

        for truck in self.trucks:
            valid_route = None
            attempts = 0
            
            while not valid_route and attempts < 100:
                load = random.choice(loads)
                dump = random.choice(dumps)
                valid_route = RoutingService.calculate_route(
                    graph, load['coor'], dump['coor']
                )
                attempts += 1
            
            if valid_route:
                truck.assign_route(valid_route)
            else:
                truck.status = "ERROR"

    async def start(self):
        if self.is_running:
            return
            
        self._assign_random_routes()
        self.is_running = True
        asyncio.create_task(self._simulation_loop())

    def stop(self):
        self.is_running = False

    async def _simulation_loop(self):
        last_time = time.time()
        
        while self.is_running:
            current_time = time.time()
           
            dt = (current_time - last_time) * self.time_multiplier 
            last_time = current_time

            for truck in self.trucks:
                if truck.status == "MOVING":
                    self._update_truck(truck, dt)
            
            await asyncio.sleep(self.update_interval)

    def _update_truck(self, truck: Truck, dt: float):
        
        speed_kmh = random.uniform(40.0, 80.0)
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