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

from django.http import JsonResponse
from .utils.gpx_parser import parse_gpx
from .utils.graph_builder import build_graph
from .algorithms.shortest_path import shortest_a_star
from .algorithms.least_turn_path import turn_a_star
from .algorithms.energy_path import elevation_a_star

def calculate_routes(request):
    try:
        # Hardcoded path for testing
        gpx_path = "D:/wayplot/campus.gpx"  # <-- replace with your actual GPX file path

        # Parse the GPX file
        points = parse_gpx(gpx_path)
        graph = build_graph(points)

        start = 0
        end = len(points) - 1

        # Run the three routing algorithms
        shortest = shortest_a_star(graph, points, start, end)
        least_turn = turn_a_star(graph, points, start, end)
        energy = elevation_a_star(graph, points, start, end)

        # Prepare the result
        result = {
            "shortest_path": [points[i] for i in shortest],
            "least_turn_path": [points[i] for i in least_turn],
            "energy_efficient_path": [points[i] for i in energy],
        }

        return JsonResponse(result)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
