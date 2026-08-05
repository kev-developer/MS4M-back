import json
import math
import networkx as nx
from typing import List, Tuple

def haversine_distance(coord1: List[float], coord2: List[float]) -> float:
    R = 6371000  # Radio de la Tierra en metros
    lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
    lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c

class GraphService:
    def __init__(self, json_path: str):
        self.graph = nx.Graph() 
        self.loads = []
        self.dumps = []
        self.routes_data = []
        
        self._load_data(json_path)

    def _load_data(self, json_path: str):
        """Carga el JSON y delega la construcción del grafo."""
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.loads = data.get('Load', [])
        self.dumps = data.get('Dump', [])
        self.routes_data = data.get('Routes', [])

        self._build_graph()

    def _build_graph(self):
        for route in self.routes_data:
            points = route.get('points', [])
            route_id = route.get('id_trm_cs')
            
            for i in range(len(points) - 1):
                node1 = tuple(points[i])
                node2 = tuple(points[i+1])

                self.graph.add_node(node1, pos=node1)
                self.graph.add_node(node2, pos=node2)

                dist = haversine_distance(points[i], points[i+1])

                self.graph.add_edge(
                    node1, 
                    node2, 
                    weight=dist,
                    route_id=route_id
                )

    def get_graph(self):
        return self.graph