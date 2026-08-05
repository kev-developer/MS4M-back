import networkx as nx
from typing import List, Tuple, Optional
from .graph_service import haversine_distance

class RoutingService:
    
    @staticmethod
    def get_nearest_node(graph: nx.Graph, coord: List[float]) -> Tuple[float, float]:
        """
        Encuentra el nodo del grafo más cercano a una coordenada dada.
        Garantiza que el inicio y fin existan en la red vial.
        """
        target_tuple = tuple(coord)
        
        if target_tuple in graph.nodes:
            return target_tuple
            
        closest_node = None
        min_dist = float('inf')
        
        for node in graph.nodes:
            dist = haversine_distance(coord, list(node))
            if dist < min_dist:
                min_dist = dist
                closest_node = node
                
        return closest_node

    @staticmethod
    def calculate_route(graph: nx.Graph, load_coord: List[float], dump_coord: List[float]) -> Optional[List[Tuple[float, float]]]:
        """
        Calcula la ruta más corta entre origen y destino cumpliendo las reglas del negocio.
        """
        start_node = RoutingService.get_nearest_node(graph, load_coord)
        end_node = RoutingService.get_nearest_node(graph, dump_coord)
        
        if not start_node or not end_node:
            return None

        if not nx.has_path(graph, start_node, end_node):
            return None
            
        try:
            path = nx.shortest_path(
                graph, 
                source=start_node, 
                target=end_node, 
                weight='weight',
                method='dijkstra'
            )
            return path
        except nx.NetworkXNoPath:
            return None