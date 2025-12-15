# from django.shortcuts import render

# # Create your views here.
# from django.http import JsonResponse
# from .utils.gpx_parser import parse_gpx
# from .utils.graph_builder import build_graph
# from .algorithms.shortest_path import shortest_a_star
# from .algorithms.least_turn_path import turn_a_star
# from .algorithms.energy_path import elevation_a_star

# def calculate_routes(request):
#     try:
#         gpx_path = request.GET.get("gpx")

#         if not gpx_path:
#             return JsonResponse({"error": "GPX file path required"}, status=400)

#         points = parse_gpx(gpx_path)
#         graph = build_graph(points)

#         start = 0
#         end = len(points) - 1

#         shortest = shortest_a_star(graph, points, start, end)
#         least_turn = turn_a_star(graph, points, start, end)
#         energy = elevation_a_star(graph, points, start, end)

#         result = {
#             "shortest_path": [points[i] for i in shortest],
#             "least_turn_path": [points[i] for i in least_turn],
#             "energy_efficient_path": [points[i] for i in energy],
#         }

#         return JsonResponse(result)
    
#     except Exception as e:
#         return JsonResponse({"error": str(e)}, status=500)

# from django.http import JsonResponse
# from .utils.gpx_parser import parse_gpx
# from .utils.graph_builder import build_graph
# from .algorithms.shortest_path import shortest_a_star
# from .algorithms.least_turn_path import turn_a_star
# from .algorithms.energy_path import elevation_a_star

# def calculate_routes(request):
#     try:
#         # Hardcoded path for testing
#         gpx_path = "D:/wayplot/campus.gpx"  # <-- replace with your actual GPX file path

#         # Parse the GPX file
#         points = parse_gpx(gpx_path)
#         graph = build_graph(points)

#         start = 0
#         end = len(points) - 1

#         # Run the three routing algorithms
#         shortest = shortest_a_star(graph, points, start, end)
#         least_turn = turn_a_star(graph, points, start, end)
#         energy = elevation_a_star(graph, points, start, end)

#         # Prepare the result
#         result = {
#             "shortest_path": [points[i] for i in shortest],
#             "least_turn_path": [points[i] for i in least_turn],
#             "energy_efficient_path": [points[i] for i in energy],
#         }

#         return JsonResponse(result)

#     except Exception as e:
#         return JsonResponse({"error": str(e)}, status=500)


# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# from .utils.gpx_parser import parse_gpx


# # from .gpx_parser import parse_gpx
# # from .graph import build_graph

# from .algorithms.shortest_path import shortest_a_star
# from .algorithms.energy_path import elevation_a_star
# from .algorithms.least_turn_path import turn_a_star

# # -------- GLOBAL MEMORY --------
# GRAPH = None
# POINTS = None


# @csrf_exempt
# def upload_gpx(request):
#     global GRAPH, POINTS

#     if request.method != "POST":
#         return JsonResponse({"error": "POST required"}, status=405)

#     gpx_file = request.FILES.get("file")
#     if not gpx_file:
#         return JsonResponse({"error": "No GPX file"}, status=400)

#     points_list = parse_gpx(gpx_file)

#     POINTS = {i: p for i, p in enumerate(points_list)}
#     GRAPH = build_graph(points_list)

#     return JsonResponse({
#         "message": "GPX loaded successfully",
#         "nodes": len(POINTS)
#     })


# def find_path(request):
#     if GRAPH is None or POINTS is None:
#         return JsonResponse({"error": "Upload GPX first"}, status=400)

#     start = int(request.GET.get("start"))
#     end = int(request.GET.get("end"))
#     mode = request.GET.get("mode", "shortest")

#     if mode == "shortest":
#         path = shortest_a_star(GRAPH, POINTS, start, end)
#     elif mode == "least_turn":
#         path = turn_a_star(GRAPH, POINTS, start, end)
#     elif mode == "energy":
#         path = elevation_a_star(GRAPH, POINTS, start, end)
#     else:
#         return JsonResponse({"error": "Invalid mode"}, status=400)

#     return JsonResponse({
#         "mode": mode,
#         "nodes": path,
#         "coordinates": [POINTS[n][:2] for n in path]
#     })



from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import math
import heapq
import xml.etree.ElementTree as ET
import requests
from io import BytesIO

# ================== GLOBAL MEMORY ==================
GRAPH = None
POINTS = None


# ================== GPX PARSER ==================
def parse_gpx_from_url(gpx_url):
    response = requests.get(gpx_url, timeout=15)
    response.raise_for_status()

    tree = ET.parse(BytesIO(response.content))
    root = tree.getroot()

    namespace = {'default': 'http://www.topografix.com/GPX/1/1'}
    points = []

    for trk in root.findall('default:trk', namespace):
        for trkseg in trk.findall('default:trkseg', namespace):
            for trkpt in trkseg.findall('default:trkpt', namespace):
                lat = float(trkpt.get('lat'))
                lon = float(trkpt.get('lon'))

                ele_tag = trkpt.find('default:ele', namespace)
                ele = float(ele_tag.text) if ele_tag is not None else 0.0

                points.append((lat, lon, ele))

    return points


# ================== GRAPH BUILDER ==================
def build_graph(points):
    graph = {}
    for i in range(len(points) - 1):
        graph.setdefault(i, []).append(i + 1)
        graph.setdefault(i + 1, []).append(i)
    return graph


# ================== NEAREST NODE ==================
def find_nearest_node(points, lat, lon):
    min_dist = float("inf")
    nearest = 0

    for i, (plat, plon, _) in enumerate(points):
        d = math.hypot(plat - lat, plon - lon)
        if d < min_dist:
            min_dist = d
            nearest = i

    return nearest


# ================== IMPORT ALGORITHMS ==================
from .algorithms.shortest_path import shortest_a_star
from .algorithms.least_turn_path import turn_a_star
from .algorithms.energy_path import elevation_a_star


# ================== LOAD GPX (CLOUDINARY) ==================
@csrf_exempt
def upload_gpx(request):
    global GRAPH, POINTS

    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    data = json.loads(request.body)
    gpx_url = data.get("gpx_url")

    if not gpx_url:
        return JsonResponse({"error": "gpx_url required"}, status=400)

    points_list = parse_gpx_from_url(gpx_url)

    POINTS = {i: p for i, p in enumerate(points_list)}
    GRAPH = build_graph(points_list)

    return JsonResponse({
        "message": "GPX loaded from Cloudinary",
        "nodes": len(POINTS)
    })


# ================== FIND PATH ==================
def find_path(request):
    if GRAPH is None or POINTS is None:
        return JsonResponse({"error": "Load GPX first"}, status=400)

    try:
        start = int(request.GET.get("start"))
        end = int(request.GET.get("end"))
    except (TypeError, ValueError):
        return JsonResponse({"error": "start & end required"}, status=400)

    mode = request.GET.get("mode", "shortest")

    if mode == "shortest":
        path = shortest_a_star(GRAPH, POINTS, start, end)
    elif mode == "least_turn":
        path = turn_a_star(GRAPH, POINTS, start, end)
    elif mode == "energy":
        path = elevation_a_star(GRAPH, POINTS, start, end)
    else:
        return JsonResponse({"error": "Invalid mode"}, status=400)

    return JsonResponse({
        "mode": mode,
        "nodes": path,
        "coordinates": [POINTS[n][:2] for n in path]
    })

