from http.client import HTTPException
import io
import os
from typing import Optional
from django.http import HttpResponseNotAllowed, JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .utils.routingUtil import GraphData, load_and_prepare_graph, haversine_distance, parse_gpx_content
from .utils.graph_builder import build_graph
from .algorithms.shortest_path import shortest_a_star
from .algorithms.least_turn_path import turn_a_star
from .algorithms.energy_path import elevation_a_star
from .utils.routingUtil import *
import cloudinary.uploader
import json

cloudinary.config( 
    cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key = os.environ.get('CLOUDINARY_API_KEY'),
    api_secret = os.environ.get('CLOUDINARY_API_SECRET'),
    secure = True
)

def health_check(request):
    return HttpResponse("Wayplot Django backend is healthy.", content_type="text/plain")

@csrf_exempt
def calculate_routes(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    
    try:
        # --- PARSE REQUEST ---
        data = json.loads(request.body)
        map_url = data.get("map_url")
        source_id = int(data.get("source_id"))
        target_id = int(data.get("target_id"))
        mode = data.get("mode", "shortest")

        if (map_url is None) or (source_id is None) or (target_id is None):
            return JsonResponse(status=400, data={"error": "Missing required parameters in request."})

        if not map_url:
            return JsonResponse(status=400, data={"error": "Missing map_url in request. Cannot load graph data."})
        
        try:
            # Load the graph. This function uses the internal cache 
            # (GraphData.last_url) to avoid re-fetching if the URL hasn't changed.
            load_and_prepare_graph(map_url)
        except Exception as e:
            # Re-raise error if fetching the graph data fails
            raise e


        # --- INPUT VALIDATION ---
        if source_id not in GraphData.node_coords or target_id not in GraphData.node_coords:
            return JsonResponse(status=400, data={"error": "Source or Target Node ID not found in graph."})

        # --- ROUTING LOGIC ---
        turn_count = 0 # Initialize turn_count
        
        if mode == 'shortest':
            path_ids, cost = shortest_path_astar(source_id, target_id, GraphData)
            cost_units = "meters"
        elif mode == 'energy_efficient':
            path_ids, cost = energy_efficient_astar(source_id, target_id, GraphData)
            cost_units = "E-units"
        elif mode == 'least_turn':
            path_ids, cost, turn_count = least_turn_astar(source_id, target_id, GraphData) 
            cost_units = "Weighted-Units"
        else:
            return JsonResponse(status=400, data={"error": f"Invalid routing mode: {mode}"})

        if not path_ids:
            return JsonResponse(status=404, data={"error": "No path found between selected nodes."})

        # --- POST-PROCESSING ---
        path_coords: List[Tuple[float, float]] = []
        total_physical_distance: float = 0.0

        for i in range(len(path_ids)):
            node_id = path_ids[i]
            coords = GraphData.node_coords.get(node_id)
            if coords:
                path_coords.append(coords)
                
                # Calculate total physical distance
                if i > 0:
                    prev_coords = path_coords[i-1]
                    distance = haversine_distance(prev_coords[0], prev_coords[1], coords[0], coords[1])
                    total_physical_distance += distance

        # --- RETURN RESPONSE ---
        return JsonResponse(
            status=200, 
            data={
                "status": "Success",
                "mode": mode,
                "path_node_ids": path_ids,
                "path_coords": path_coords,
                "total_cost": cost, # The output of A* (which is adjusted distance/cost)
                "total_physical_distance": total_physical_distance, # Pure physical distance (meters)
                "units": cost_units,
                "turn_count": turn_count
            }
        )

    except Exception as e:
        print(e)
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
async def upload_gpx(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    gpx_file = request.FILES.get("gpx_file")
    if gpx_file is None:
        return JsonResponse(status=400, data={"error": "No GPX file uploaded."})
    
    
    if gpx_file.content_type not in ["application/gpx+xml", "application/xml"] and not gpx_file.name.endswith(".gpx"):
        return JsonResponse(status=400, data={"error": "Invalid file type. Please upload a GPX file."})
        
    # Read the content once
    gpx_content = gpx_file.read()
    print(f"Received GPX file of size: {len(gpx_content)} bytes")
    
    # --- A. UPLOAD RAW GPX FILE FIRST ---
    try:
        # Create a new stream for the first upload (Cloudinary consumes the stream)
        gpx_stream = io.BytesIO(gpx_content)
        
        # NOTE: Using standard upload() but setting resource_type='raw'
        gpx_upload_result = cloudinary.uploader.upload(
            gpx_stream,
            resource_type="raw", 
            public_id=f"raw_gpx/{gpx_file.name.split('.')[0]}_{os.urandom(4).hex()}", # Use a unique ID to avoid overwriting issues
            folder="gpx_graphs",
            overwrite=True
        )
        # FIX: Access the secure_url directly, as the standard upload() function returns a dictionary.
        cloudinary_gpx_url = gpx_upload_result['secure_url'] 

    except Exception as e:
        print(f"GPX Upload Error (Credentials/Network): {e}")
        return JsonResponse(status=500, data={"error": "Failed to upload raw GPX file to Cloudinary. Check credentials/network."})


    # --- B. PARSE AND BUILD GRAPH (Using your existing logic) ---
    tracks = parse_gpx_content(gpx_content)
    if not tracks:
         return JsonResponse(status=400, data={"error": "GPX file contained no valid track segments."})
    
    graph_data = build_graph(tracks)
    
    # C. CONVERT TO JSON BYTES
    json_data = json.dumps(graph_data, indent=2)
    json_bytes = json_data.encode('utf-8')
    
    # --- D. UPLOAD CONVERTED JSON FILE ---
    try:
        # Create a new stream for the second upload
        json_stream = io.BytesIO(json_bytes)
        
        # NOTE: Using standard upload()
        json_upload_result = cloudinary.uploader.upload(
            json_stream,
            resource_type="raw", 
            public_id=f"json_graph/{gpx_file.name.split('.')[0]}",
            folder="gpx_graphs",             
            overwrite=True                   
        )
        cloudinary_json_url = json_upload_result['secure_url'] 

    except Exception as e:
        print(f"JSON Upload Error: {e}")
        return JsonResponse(status=500, data={"error": "Failed to upload converted JSON file to Cloudinary."})

    print("------------ STart of graph -------------")
    print(graph_data)
    print("------------ End of graph -------------")
    # --- E. RETURN RESPONSE ---
    return JsonResponse(
        status=200,
        data={
            "status": "Success",
            "message": "GPX converted and uploaded successfully.",
            "cloudinary_gpx_url": cloudinary_gpx_url,
            "cloudinary_json_url": cloudinary_json_url,
        }
    )