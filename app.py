# Flask backend that loads map data, handles API requests, validates inputs, and runs the appropriate search algorithm.

import json
from flask import Flask, jsonify, render_template, request
from uninformed import bfs, dfs, ucs, ids
from informed import greedy_bfs, astar

app = Flask(__name__)

with open("map_data.json", "r", encoding="utf-8") as f:
    GRAPH = json.load(f)

# Represents each undirected road once, even though the graph stores both directions.
def unique_connections(graph):
    seen_pairs = set()
    for source, targets in graph["edges"].items():
        for destination in targets:
            seen_pairs.add(frozenset((source, destination)))
    return [sorted(pair) for pair in seen_pairs]


UNIQUE_CONNECTIONS = unique_connections(GRAPH)

GRAPH_SUMMARY = {
    "total_cities": len(GRAPH["locations"]),
    "total_edges": len(UNIQUE_CONNECTIONS),
    "edges": UNIQUE_CONNECTIONS,
}

# Maps the short string a frontend dropdown would send ("bfs") to the real Python function that runs it.
ALGORITHMS = {
    "bfs": bfs,
    "dfs": dfs,
    "ucs": ucs,
    "ids": ids,
    "greedy": greedy_bfs,
    "astar": astar,
}

# A friendlier name for each, to show back to the user.
ALGORITHM_DISPLAY_NAMES = {
    "bfs": "BFS",
    "dfs": "DFS",
    "ucs": "UCS",
    "ids": "IDS",
    "greedy": "Greedy Best-First Search",
    "astar": "A*",
}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/locations")
def locations():
    return jsonify(GRAPH["locations"])


@app.route("/api/graph_summary")
def graph_summary():
    return jsonify(GRAPH_SUMMARY)

# Combines stored OSRM geometries into the complete curved route, reusing and reversing the opposite edge’s geometry when needed.
def build_route_geometry(path):
    coords = []
    for i in range(len(path) - 1):
        current_city, next_city = path[i], path[i + 1]
        edge = GRAPH["edges"].get(current_city, {}).get(next_city)
        if edge and "geometry" in edge:
            coords.extend(edge["geometry"])
            continue
        reverse_edge = GRAPH["edges"].get(next_city, {}).get(current_city)
        if reverse_edge and "geometry" in reverse_edge:
            coords.extend(reversed(reverse_edge["geometry"]))
            continue
        return []
    return coords

# Calculates the real road distance for each route segment and provides a per-leg distance breakdown.
def build_leg_distances(graph, path):
    return [round(graph["edges"][path[i]][path[i + 1]]["distance_km"], 2)
            for i in range(len(path) - 1)]


# Validates all search request inputs and always returns clean JSON without crashing.
@app.route("/api/search", methods=["POST"])
def search():
    data = request.get_json(silent=True) or {}

    source = data.get("source")
    destination = data.get("destination")
    algorithm_key = data.get("algorithm")

    if not source or not destination or not algorithm_key:
        return jsonify({"error": "Request must include 'source', 'destination', and 'algorithm'."}), 400

    if source not in GRAPH["locations"]:
        return jsonify({"error": f"Unknown source location: '{source}'"}), 400

    if destination not in GRAPH["locations"]:
        return jsonify({"error": f"Unknown destination location: '{destination}'"}), 400

    if algorithm_key not in ALGORITHMS:
        valid_options = ", ".join(ALGORITHMS.keys())
        return jsonify({"error": f"Unknown algorithm '{algorithm_key}'. Valid options: {valid_options}"}), 400

    algorithm_function = ALGORITHMS[algorithm_key]
    result = algorithm_function(GRAPH, source, destination)

    if result is None:
        return jsonify({
            "algorithm": ALGORITHM_DISPLAY_NAMES[algorithm_key],
            "source": source,
            "destination": destination,
            "path": None,
            "cost": None,
            "nodes_expanded": None,
            "message": f"No path exists from {source} to {destination} in this graph.",
        })

    return jsonify({
        "algorithm": ALGORITHM_DISPLAY_NAMES[algorithm_key],
        "source": source,
        "destination": destination,
        "path": result["path"],
        "cost": round(result["cost"], 2),
        "nodes_expanded": result["nodes_expanded"],
        "exploration_order": result["exploration_order"],
        "exploration_distances": [round(d, 2) for d in result["exploration_distances"]],
        "edges_evaluated": result["edges_evaluated"],
        "leg_distances": build_leg_distances(GRAPH, result["path"]),
        "route_geometry": build_route_geometry(result["path"]),
    })


if __name__ == "__main__":
    app.run(debug=True)
