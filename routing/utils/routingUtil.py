import math
import heapq
from typing import Dict, Any, List, Tuple, Optional
from django.forms import ValidationError
import requests
import xml.etree.ElementTree as ET
import io
from http.client import HTTPException

class GraphData:
    """Holds the graph data, adjacency lists, and node coordinates."""
    nodes: List[Dict[str, Any]] = []
    node_coords: Dict[int, Tuple[float, float]] = {}
    graph_adj: Dict[int, List[Tuple[int, float]]] = {}
    physical_dist_adj: Dict[int, Dict[int, float]] = {}
    last_url: str = ""

# --- 4. CORE ALGORITHMS AND HELPERS ---

# Constants for cost functions
ENERGY_PENALTY_FACTOR = 1.2
TURN_PENALTY_METERS = 50.0
EARTH_RADIUS_METERS = 6371e3 # Earth radius in meters

def haversine_distance(lat1, lon1, lat2, lon2) -> float:
    """Calculate the distance (in meters) between two points on the earth."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return EARTH_RADIUS_METERS * c

def calculate_initial_heading(lat1, lon1, lat2, lon2):
    """Calculate the initial bearing between two points (in radians)."""
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    y = math.sin(lon2 - lon1) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(lon2 - lon1)
    
    return math.atan2(y, x)

# --- Update energy_efficient_astar in main.py ---

def energy_efficient_astar(start_id: int, goal_id: int, nodes_data: GraphData) -> Tuple[List[int], float]:
    """Finds the path using physical distance adjusted by ENERGY_PENALTY_FACTOR (1.2)."""
    
    # Create a temporary graph where weights are adjusted for energy penalty
    adjusted_adj = {}
    for u, edges in nodes_data.graph_adj.items():
        # Adjust the 'weight' field (cost) by the penalty factor
        adjusted_adj[u] = [(v, w * ENERGY_PENALTY_FACTOR) for v, w in edges]

    # Run A* on the adjusted graph. 
    # NOTE: The base shortest_path_astar implementation is used, 
    # but with the energy-penalized graph.
    path, cost = shortest_path_astar(start_id, goal_id, nodes_data, adj_list=adjusted_adj)
    
    return path, cost


# --- CRITICAL: Update shortest_path_astar to accept an optional custom adjacency list ---
# (This allows us to reuse the A* logic for different modes)

def shortest_path_astar(start_id: int, goal_id: int, nodes_data: GraphData, adj_list: Optional[Dict[int, List[Tuple[int, float]]]] = None) -> Tuple[List[int], float]:
    """
    Finds the shortest path using the provided adjacency list (or default).
    """
    adj = adj_list if adj_list is not None else nodes_data.graph_adj
    
    open_set = []
    heapq.heappush(open_set, (0, start_id))
    came_from = {}
    g_score = {n['id']: float('inf') for n in nodes_data.nodes}
    g_score[start_id] = 0

    while open_set:
        _, current = heapq.heappop(open_set)

        if current == goal_id:
            path = []
            current_path_node = current
            while current_path_node in came_from:
                path.append(current_path_node)
                current_path_node = came_from[current_path_node]
            path.append(start_id)
            return path[::-1], g_score[goal_id]

        for neighbor, weight in adj.get(current, []): # Use the passed-in adj list
            # ... (rest of A* logic remains the same)
            tentative_g = g_score[current] + weight
            if tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                
                # Heuristic (straight-line physical distance to goal)
                lat1, lon1 = nodes_data.node_coords[neighbor]
                lat2, lon2 = nodes_data.node_coords[goal_id]
                h = haversine_distance(lat1, lon1, lat2, lon2)
                
                f_score = tentative_g + h
                heapq.heappush(open_set, (f_score, neighbor))
    
    return [], float('inf')

# --- Update least_turn_astar in main.py ---
# ... (near the top with other helpers like haversine_distance) ...




# --- Define constants used in Least Turn ---
# --- Define constants used in Least Turn ---
TURN_PENALTY_METERS = 50.0  # Cost added for a sharp turn
SHARP_TURN_THRESHOLD_DEG = 45 # Angle threshold for a turn to be considered 'sharp'
NO_PREV_NODE = -1 

# Make sure this helper function is defined correctly in your main.py!
def calculate_initial_heading(lat1, lon1, lat2, lon2):
    """Calculate the initial bearing between two points (in radians)."""
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    y = math.sin(lon2 - lon1) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(lon2 - lon1)
    
    return math.atan2(y, x) 

# --- Corrected least_turn_astar ---

# --- 4. CORE ALGORITHMS AND HELPERS (Modify least_turn_astar) ---

def least_turn_astar(start_id: int, goal_id: int, nodes_data: GraphData) -> Tuple[List[int], float, int]: # <<< CHANGED RETURN TYPE
    """ Finds the path prioritizing minimal turns by adding a penalty. """
    open_set = []
    heapq.heappush(open_set, (0, start_id, NO_PREV_NODE))
    g_score: Dict[Tuple[int, int], float] = {}
    g_score[(start_id, NO_PREV_NODE)] = 0
    final_parent: Dict[int, int] = {}
    final_cost: Dict[int, float] = {start_id: 0}
    
    # NEW: Dictionary to track the minimum turn count to reach each node
    turn_count_to_node: Dict[int, int] = {start_id: 0} 

    while open_set:
        _, current, previous = heapq.heappop(open_set)
        current_state = (current, previous)
        
        if g_score[current_state] > final_cost.get(current, float('inf')): continue

        if current == goal_id:
            path = []
            temp = current
            while temp != start_id:
                path.append(temp)
                temp = final_parent.get(temp, NO_PREV_NODE)
                if temp == NO_PREV_NODE: return [], final_cost[goal_id], 0 # Error path
            path.append(start_id)
            
            # Return the path, the total cost, and the total turn count
            return path[::-1], final_cost[goal_id], turn_count_to_node.get(goal_id, 0) # <<< CHANGED RETURN VALUE

        for neighbor, base_weight in nodes_data.graph_adj.get(current, []):
            if neighbor == previous and current != start_id: continue

            turn_penalty = 0.0
            is_turn = False # NEW: Flag to track if a turn occurred
            
            if previous != NO_PREV_NODE:
                lat_prev, lon_prev = nodes_data.node_coords[previous]
                lat_curr, lon_curr = nodes_data.node_coords[current]
                lat_next, lon_next = nodes_data.node_coords[neighbor]

                heading1 = calculate_initial_heading(lat_prev, lon_prev, lat_curr, lon_curr)
                heading2 = calculate_initial_heading(lat_curr, lon_curr, lat_next, lon_next)
                
                angle_change = abs(heading2 - heading1)
                if angle_change > math.pi: angle_change = 2 * math.pi - angle_change
                
                if math.degrees(angle_change) > SHARP_TURN_THRESHOLD_DEG:
                    turn_penalty = TURN_PENALTY_METERS 
                    is_turn = True # Set flag if turn is detected
                    
            cost = base_weight + turn_penalty
            tentative_g = g_score.get(current_state, float('inf')) + cost
            neighbor_state = (neighbor, current)
            
            # NEW: Calculate tentative turn count
            current_turn_count = turn_count_to_node.get(current, 0)
            tentative_turn_count = current_turn_count + (1 if is_turn else 0)

            if tentative_g < g_score.get(neighbor_state, float('inf')):
                g_score[neighbor_state] = tentative_g
                
                if tentative_g < final_cost.get(neighbor, float('inf')):
                    final_cost[neighbor] = tentative_g
                    final_parent[neighbor] = current 
                    
                    # Update turn count for the node on the best current path
                    turn_count_to_node[neighbor] = tentative_turn_count # NEW LINE

                lat_next, lon_next = nodes_data.node_coords[neighbor]
                lat_goal, lon_goal = nodes_data.node_coords[goal_id]
                h = haversine_distance(lat_next, lon_next, lat_goal, lon_goal)
                
                f_score = tentative_g + h
                heapq.heappush(open_set, (f_score, neighbor, current))

    return [], float('inf'), 0 # <<< CHANGED RETURN VALUE


def load_and_prepare_graph(map_url: str):
    """Fetches graph data, computes physical distances, and prepares for routing."""
    if map_url == GraphData.last_url and GraphData.nodes:
        # Cache hit: graph already loaded
        return

    try:
        response = requests.get(map_url)
        response.raise_for_status() 
        data = response.json()
    except requests.RequestException as e:
        raise ValidationError(f"Failed to fetch graph data from URL: {e}")

    # Reset cache and populate new data
    GraphData.nodes = data.get('nodes', [])
    GraphData.graph_adj = {}
    GraphData.node_coords = {}
    GraphData.physical_dist_adj = {}
    
    # 1. Map Node ID to Coordinates (and vice versa)
    for node in GraphData.nodes:
        node_id = node['id']
        GraphData.node_coords[node_id] = (node['lat'], node['lon'])

    # 2. Build Adjacency List (A* graph input) and physical distance map
    for edge in data.get('edges', []):
        u, v, weight = edge['u'], edge['v'], edge['weight']

        # Determine the cost/weight for shortest path (using the provided 'weight' field, assumed to be distance)
        cost = weight 
        
        # Build directed graph adjacency list (for A*)
        if u not in GraphData.graph_adj: GraphData.graph_adj[u] = []
        if v not in GraphData.graph_adj: GraphData.graph_adj[v] = []
        
        GraphData.graph_adj[u].append((v, cost))
        GraphData.graph_adj[v].append((u, cost)) # Assuming undirected graph for simplicity

    GraphData.last_url = map_url
    # Status check
    if not GraphData.nodes:
        raise ValidationError("Graph data loaded but is empty.")


def parse_gpx_content(gpx_content: bytes) -> List[List[Tuple[float, float]]]:
    """Parses raw GPX content (bytes) into a list of track segments."""
    try:
        print("Parsing GPX content...")
        print(gpx_content.decode('utf-8', errors='ignore'))  # Print GPX content for debugging
        # Use io.BytesIO to treat the bytes content as a file
        tree = ET.parse(io.BytesIO(gpx_content))
        root = tree.getroot()
        # Handle GPX namespaces
        ns = {'gpx': 'http://www.topografix.com/GPX/1/1'}
        tracks = []

        for trk in root.findall('.//gpx:trk', ns):
            for trkseg in trk.findall('.//gpx:trkseg', ns):
                segment = []
                for trkpt in trkseg.findall('.//gpx:trkpt', ns):
                    lat = float(trkpt.get('lat'))
                    lon = float(trkpt.get('lon'))
                    segment.append((lat, lon))
                
                if segment:
                    tracks.append(segment)
        
        print("Finished parsing GPX content.")
        print(tracks)
        print("End of parsed tracks.")
        return tracks
    except ET.ParseError:
        raise ValidationError("Invalid GPX file format.")
    except Exception as e:
        raise ValidationError(f"Error parsing GPX content: {e}")
