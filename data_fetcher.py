# Builds map_data.json: geocodes Myanmar towns with Nominatim, then
# fetches real road distances between them with OSRM.

import json
import time
import os
from datetime import datetime, timezone
import requests

MAP_DATA_FILE = "map_data.json"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OSRM_URL = "http://router.project-osrm.org/route/v1/driving"

HEADERS = {
    "User-Agent": "MyanmarSearchVisualizer-StudentProject/1.0 (contact: ohnmarnyuntsan@gmail.com)"
}

# More than 20 locations across the states and regions of Myanmar.
LOCATIONS = {
    "Yangon":       {"region": "Yangon Region"},
    "Kalay":        {"region": "Sagaing Region"},
    "Hakha":        {"region": "Chin State"},
    "Kyaikto":      {"region": "Mon State"},
    "Naypyidaw":    {"region": "Naypyidaw UT"},
    "Meiktila":     {"region": "Mandalay Region"},
    "Mandalay":     {"region": "Mandalay Region"},
    "Myitkyina":    {"region": "Kachin State"},
    "Bhamo":        {"region": "Kachin State"},
    "Hpakant":      {"region": "Kachin State"},
    "Sagaing":      {"region": "Sagaing Region"},
    "Pyin Oo Lwin": {"region": "Mandalay Region"},
    "Bagan":        {"region": "Mandalay Region"},
    "Kyaukpadaung": {"region": "Mandalay Region"},
    "Pyay":         {"region": "Bago Region"},
    "Monywa":       {"region": "Sagaing Region"},
    "Kalaw":        {"region": "Shan State"},
    "Taunggyi":     {"region": "Shan State"},
    "Hsipaw":       {"region": "Shan State"},
    "Lashio":       {"region": "Shan State"},
    "Mawlamyine":   {"region": "Mon State"},
    "Hpa-An":       {"region": "Kayin State"},
    "Dawei":        {"region": "Tanintharyi Region"},
    "Myeik":        {"region": "Tanintharyi Region"},
    "Pathein":      {"region": "Ayeyarwady Region"},
    "Bago":         {"region": "Bago Region"},
    "Taungoo":      {"region": "Bago Region"},
    "Sittwe":       {"region": "Rakhine State"},
    "Loikaw":       {"region": "Kayah State"},
}

# Real road connections to query between locations. These are directed edges, but will store them in both directions.
EDGES_TO_QUERY = [
    ("Yangon", "Bago"), ("Yangon", "Pyay"), ("Yangon", "Taungoo"), ("Yangon", "Pathein"),
    ("Bago", "Taungoo"), ("Bago", "Kyaikto"),
    ("Kyaikto", "Hpa-An"), ("Kyaikto", "Mawlamyine"),
    ("Mawlamyine", "Hpa-An"), ("Mawlamyine", "Dawei"), ("Dawei", "Myeik"),
    ("Pathein", "Sittwe"), ("Pathein", "Pyay"),
    ("Sittwe", "Pyay"), ("Sittwe", "Hakha"), ("Sittwe", "Bagan"), ("Sittwe", "Kyaukpadaung"),
    ("Hakha", "Kalay"), ("Hakha", "Monywa"), ("Kalay", "Monywa"),
    ("Taungoo", "Naypyidaw"), ("Taungoo", "Loikaw"), ("Taungoo", "Pyay"),
    ("Pyay", "Bagan"), ("Pyay", "Naypyidaw"), ("Pyay", "Kyaukpadaung"),
    ("Meiktila", "Mandalay"), ("Meiktila", "Kalaw"), ("Meiktila", "Kyaukpadaung"),
    ("Naypyidaw", "Meiktila"), ("Naypyidaw", "Kalaw"), ("Naypyidaw", "Loikaw"), ("Naypyidaw", "Sittwe"),
    ("Kalaw", "Taunggyi"), ("Kalaw", "Loikaw"), ("Taunggyi", "Loikaw"), ("Taunggyi", "Hsipaw"),
    ("Mandalay", "Sagaing"), ("Mandalay", "Kalaw"), ("Mandalay", "Bhamo"),
    ("Pyin Oo Lwin", "Taunggyi"),
    ("Bhamo", "Myitkyina"), ("Myitkyina", "Hpakant"), ("Bhamo", "Lashio"),
    ("Kalay", "Hpakant"),
    ("Mandalay", "Pyin Oo Lwin"), ("Pyin Oo Lwin", "Hsipaw"), ("Hsipaw", "Lashio"),
    ("Monywa", "Bagan"), ("Monywa", "Sagaing"),
    ("Mandalay", "Bagan"), ("Bagan", "Kyaukpadaung"),
]


def load_map_data():
    if os.path.exists(MAP_DATA_FILE):
        with open(MAP_DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"locations": {}, "edges": {}, "meta": {}}


def save_map_data(data):
    with open(MAP_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))


def _nominatim_request(params):
    # Rate limit applies even on failure, so always sleep after.
    try:
        response = requests.get(NOMINATIM_URL, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        results = response.json()
    except requests.RequestException as e:
        print(f"    [ERROR] Nominatim request failed: {e}")
        results = []
    time.sleep(1)
    return results[0] if results else None


def geocode(place_name, existing_locations, search_override=None, extra_params=None, manual_coords=None):
    # Returns {lat, lon, display_name} for a place, or None if not found.
    cached = existing_locations.get(place_name)
    if cached and "display_name" in cached:
        print(f"  [cache] {place_name} -> {cached['display_name']}")
        return cached

    if manual_coords is not None:
        lat, lon = manual_coords
        entry = {"lat": float(lat), "lon": float(lon),
                 "display_name": f"{place_name} (manually pinned - user-verified coordinates)"}
        print(f"  [manual] {place_name} -> lat={entry['lat']}, lon={entry['lon']} (Nominatim skipped)")
        return entry

    # Structured city search first, then fall back to a free-text search.
    match = None
    if search_override is None:
        params = {"city": place_name, "country": "Myanmar", "format": "json", "limit": 1}
        if extra_params:
            params.update(extra_params)
        match = _nominatim_request(params)
    if match is None:
        query_text = search_override if search_override else f"{place_name}, Myanmar"
        params = {"q": query_text, "format": "json", "limit": 1}
        if extra_params:
            params.update(extra_params)
        match = _nominatim_request(params)

    if match is None:
        print(f"  [ERROR] Nominatim found nothing for '{place_name}'")
        return None

    entry = {"lat": float(match["lat"]), "lon": float(match["lon"]), "display_name": match.get("display_name", "")}
    print(f"  [live]  {place_name} -> lat={entry['lat']}, lon={entry['lon']}")
    print(f"          matched: \"{entry['display_name']}\"")
    return entry


def get_route(name1, coord1, name2, coord2, existing_edges):
    # Returns (distance_km, geometry) using OSRM, or (None, None) on failure.
    cached = existing_edges.get(name1, {}).get(name2)
    if cached and cached.get("source") == "osrm" and "geometry" in cached:
        print(f"  [cache] {name1} <-> {name2}: {cached['distance_km']} km, {len(cached['geometry'])} route points")
        return cached["distance_km"], cached["geometry"]

    lat1, lon1 = coord1
    lat2, lon2 = coord2
    url = f"{OSRM_URL}/{lon1},{lat1};{lon2},{lat2}"
    print(f"URL from {name1} to {name2}: {url}")

    try:
        response = requests.get(url, params={"overview": "full", "geometries": "geojson"},
                                 headers=HEADERS, timeout=15)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        print(f"  [ERROR] OSRM request failed for {name1} <-> {name2}: {e}")
        return None, None

    if data.get("code") != "Ok" or not data.get("routes"):
        print(f"  [ERROR] OSRM found no route between {name1} and {name2} (code={data.get('code')})")
        return None, None

    route = data["routes"][0]
    distance_km = round(route["distance"] / 1000, 1)
    # OSRM gives [lon, lat]; Leaflet needs [lat, lon].
    geometry = [[point[1], point[0]] for point in route["geometry"]["coordinates"]]

    print(f"  [live]  {name1} <-> {name2}: {distance_km} km, {len(geometry)} route points")
    time.sleep(1)
    return distance_km, geometry


if __name__ == "__main__":
    existing = load_map_data()

    print("=" * 70)
    print(f"STEP 1 - Geocoding {len(LOCATIONS)} locations")
    print("=" * 70)
    locations_out = {}
    coords = {}
    failed_locations = []

    for name, metadata in LOCATIONS.items():
        metadata = dict(metadata)
        search_override = metadata.pop("query", None)
        extra_params = metadata.pop("extra_params", None)
        manual_coords = metadata.pop("manual_coords", None)
        entry = geocode(name, existing["locations"], search_override=search_override,
                         extra_params=extra_params, manual_coords=manual_coords)
        if entry is None:
            print(f"  -> Skipping {name}, it will NOT appear in map_data.json.")
            failed_locations.append(name)
            continue
        coords[name] = (entry["lat"], entry["lon"])
        locations_out[name] = {"lat": entry["lat"], "lon": entry["lon"],
                                "display_name": entry["display_name"], **metadata}

    print(f"\n{'=' * 70}\nSTEP 2 - Getting real road distances for {len(EDGES_TO_QUERY)} planned edges\n{'=' * 70}")
    edges_out = {name: {} for name in locations_out}
    failed_edges = []

    for name1, name2 in EDGES_TO_QUERY:
        if name1 not in coords or name2 not in coords:
            print(f"  -> Skipping {name1} <-> {name2}, one side failed to geocode.")
            failed_edges.append((name1, name2, "location missing"))
            continue
        distance, geometry = get_route(name1, coords[name1], name2, coords[name2], existing["edges"])
        if distance is None:
            print(f"  -> Skipping edge {name1} <-> {name2}, no route found.")
            failed_edges.append((name1, name2, "no OSRM route"))
            continue
        # Stores each road’s geometry only once and reverses it when needed, reducing storage by about half without losing data.
        edges_out[name1][name2] = {"distance_km": distance, "source": "osrm", "geometry": geometry}
        edges_out[name2][name1] = {"distance_km": distance, "source": "osrm"}

    print(f"\n{'=' * 70}\nSTEP 3 - Saving map_data.json\n{'=' * 70}")
    map_data = {
        "locations": locations_out,
        "edges": edges_out,
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "location_count": len(locations_out),
            "edge_count": sum(len(v) for v in edges_out.values()),
        },
    }
    save_map_data(map_data)

    print(f"\nSUMMARY")
    print(f"  Locations saved: {map_data['meta']['location_count']} / {len(LOCATIONS)}")
    print(f"  Directed edges saved: {int(map_data['meta']['edge_count']/2)} / {len(EDGES_TO_QUERY)}")
    if failed_locations:
        print(f"  Locations that failed to geocode: {failed_locations}")
    if failed_edges:
        print(f"  Edges that failed: {failed_edges}")
