"""
    - Greedy Best-First Search
    - A* ("A-star")
"""

import math
import heapq
from uninformed import path_cost

#Haversine formula: calculates the straight-line distance between two latitude/longitude points on Earth.
def haversine_distance(lat1, lon1, lat2, lon2):

    EARTH_RADIUS_KM = 6371.0    # Earth's average radius, in kilometers

    lat1_rad, lon1_rad = math.radians(lat1), math.radians(lon1)
    lat2_rad, lon2_rad = math.radians(lat2), math.radians(lon2)

    delta_lat = lat2_rad - lat1_rad
    delta_lon = lon2_rad - lon1_rad

    a = (math.sin(delta_lat / 2) ** 2
         + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
    c = 2 * math.asin(math.sqrt(a))

    return EARTH_RADIUS_KM * c

# h(n): estimates the straight-line distance from the current node to the goal, never exceeding the actual road distance.
def heuristic(graph, node, goal):
    n1 = graph["locations"][node]
    n2 = graph["locations"][goal]
    return haversine_distance(n1["lat"], n1["lon"], n2["lat"], n2["lon"])

# Greedy Best-First Search
def greedy_bfs(graph, start, goal):
    frontier = [(heuristic(graph, start, goal), [start])]
    visited = set()
    nodes_expanded = 0
    exploration_order = []
    exploration_distances = []
    edges_evaluated = 0

    while frontier:
        _, path = heapq.heappop(frontier)   # take whichever path's LAST STOP looks closest to goal
        current_node = path[-1]

        if current_node in visited:
            continue
        visited.add(current_node)
        nodes_expanded += 1
        exploration_order.append(current_node)
        exploration_distances.append(path_cost(graph, path))

        if current_node == goal:
            return {
                "path": path,
                "cost": path_cost(graph, path),
                "nodes_expanded": nodes_expanded,
                "exploration_order": exploration_order,
                "exploration_distances": exploration_distances,
                "edges_evaluated": edges_evaluated,
            }

        for neighbor in graph["edges"].get(current_node, {}):
            edges_evaluated += 1
            if neighbor not in visited:
                heapq.heappush(frontier, (heuristic(graph, neighbor, goal), path + [neighbor]))

    return None

# A* Search
def astar(graph, start, goal):
    start_f = heuristic(graph, start, goal)
    frontier = [(start_f, 0, [start])]   # (f = g+h, g = real cost, h = heuristic cost)
    visited = set()
    nodes_expanded = 0
    exploration_order = []
    exploration_distances = []
    edges_evaluated = 0

    while frontier:
        _, g, path = heapq.heappop(frontier)
        current_node = path[-1]

        if current_node in visited:
            continue
        visited.add(current_node)
        nodes_expanded += 1
        exploration_order.append(current_node)
        exploration_distances.append(g)

        if current_node == goal:
            return {
                "path": path,
                "cost": g,
                "nodes_expanded": nodes_expanded,
                "exploration_order": exploration_order,
                "exploration_distances": exploration_distances,
                "edges_evaluated": edges_evaluated,
            }

        for neighbor, edge in graph["edges"].get(current_node, {}).items():
            edges_evaluated += 1
            if neighbor not in visited:
                new_g = g + edge["distance_km"]
                new_f = new_g + heuristic(graph, neighbor, goal)
                heapq.heappush(frontier, (new_f, new_g, path + [neighbor]))

    return None
