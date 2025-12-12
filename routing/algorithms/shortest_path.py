import math
import heapq

def haversine(p1, p2):
    lat1, lon1 = p1[:2]
    lat2, lon2 = p2[:2]

    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (math.sin(dphi/2)**2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2)

    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))

def shortest_a_star(graph, points, start, goal):
    pq = [(0, start)]
    dist = {start: 0}
    parent = {start: None}

    while pq:
        cost, node = heapq.heappop(pq)

        if node == goal:
            break

        for neigh in graph[node]:
            d = haversine(points[node], points[neigh])
            new_cost = cost + d

            if neigh not in dist or new_cost < dist[neigh]:
                dist[neigh] = new_cost
                parent[neigh] = node
                heapq.heappush(pq, (new_cost, neigh))

    path = []
    cur = goal
    while cur is not None:
        path.append(cur)
        cur = parent[cur]
    return path[::-1]
