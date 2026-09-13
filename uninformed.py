"""
    - Breadth-First Search (BFS)
    - Depth-First Search (DFS)
    - Uniform Cost Search (UCS)
    - Iterative Deepening Search (IDS)
"""

from collections import deque
import heapq

# Add up the real road distance for a path
def path_cost(graph, path):
    total = 0
    for i in range(len(path) - 1):
        current_node = path[i]
        next_node = path[i + 1]
        total += graph["edges"][current_node][next_node]["distance_km"]
    return total

# Breadth-First Search
def bfs(graph, start, goal):
    frontier = deque()
    frontier.append([start])
    visited = {start}
    nodes_expanded = 0
    exploration_order = []
    exploration_distances = []
    edges_evaluated = 0

    while frontier:
        path = frontier.popleft()      # take the OLDEST path in the queue
        current_node = path[-1]       
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
                visited.add(neighbor)
                frontier.append(path + [neighbor])

    return None 

# Depth-First Search
def dfs(graph, start, goal):
    frontier = [[start]]           # used as a stack
    visited = {start}
    nodes_expanded = 0
    exploration_order = []
    exploration_distances = []
    edges_evaluated = 0

    while frontier:
        path = frontier.pop()          # take the NEWEST path (end of the list)
        current_node = path[-1]
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
                visited.add(neighbor)
                frontier.append(path + [neighbor])

    return None

# Uniform Cost Search
def ucs(graph, start, goal):
    frontier = [(0, [start])]    
    visited = set()
    nodes_expanded = 0
    exploration_order = []
    exploration_distances = []
    edges_evaluated = 0

    while frontier:
        cost_so_far, path = heapq.heappop(frontier)   # cheapest entry comes out automatically
        current_node = path[-1]

        if current_node in visited:
            continue   
        visited.add(current_node)
        nodes_expanded += 1
        exploration_order.append(current_node)
        exploration_distances.append(cost_so_far)

        if current_node == goal:
            return {
                "path": path,
                "cost": cost_so_far,
                "nodes_expanded": nodes_expanded,
                "exploration_order": exploration_order,
                "exploration_distances": exploration_distances,
                "edges_evaluated": edges_evaluated,
            }

        for neighbor, edge in graph["edges"].get(current_node, {}).items():
            edges_evaluated += 1
            if neighbor not in visited:
                new_cost = cost_so_far + edge["distance_km"]
                heapq.heappush(frontier, (new_cost, path + [neighbor]))

    return None

# for this one depth-limited round only - ids() below accumulates these across every round it runs.
def _depth_limited_search(graph, start, goal, limit):
    frontier = [(start, [start])]
    nodes_expanded = 0
    exploration_order = []
    exploration_distances = []
    edges_evaluated = 0

    while frontier:
        current_node, path = frontier.pop()
        nodes_expanded += 1
        exploration_order.append(current_node)
        exploration_distances.append(path_cost(graph, path))

        if current_node == goal:
            return path, nodes_expanded, exploration_order, exploration_distances, edges_evaluated

        if len(path) - 1 < limit:   
            for neighbor in graph["edges"].get(current_node, {}):
                edges_evaluated += 1
                if neighbor not in path:   
                    frontier.append((neighbor, path + [neighbor]))

    return None, nodes_expanded, exploration_order, exploration_distances, edges_evaluated

# Iterative Deepening Search
def ids(graph, start, goal):
    max_possible_depth = len(graph["locations"])
    total_nodes_expanded = 0
    total_exploration_order = []
    total_exploration_distances = []
    total_edges_evaluated = 0

    for limit in range(max_possible_depth + 1):
        (result_path, expanded_this_round, exploration_this_round,
         distances_this_round, edges_this_round) = _depth_limited_search(graph, start, goal, limit)
        total_nodes_expanded += expanded_this_round
        total_exploration_order.extend(exploration_this_round)
        total_exploration_distances.extend(distances_this_round)
        total_edges_evaluated += edges_this_round

        if result_path is not None:
            return {
                "path": result_path,
                "cost": path_cost(graph, result_path),
                "nodes_expanded": total_nodes_expanded,
                "exploration_order": total_exploration_order,
                "exploration_distances": total_exploration_distances,
                "edges_evaluated": total_edges_evaluated,
            }

    return None
