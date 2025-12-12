import math
import heapq

def elevation_cost(e1, e2):
    if e2 > e1:
        return (e2 - e1) ** 2
    return 0

def elevation_a_star(graph, points, start, goal):
    pq = [(0, start)]
    dist = {start: 0}
    parent = {start: None}

    while pq:
        cost, node = heapq.heappop(pq)

        if node == goal:
            break

        for neigh in graph[node]:
            ele1 = points[node][2]
            ele2 = points[neigh][2]

            new_cost = cost + elevation_cost(ele1, ele2)

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
