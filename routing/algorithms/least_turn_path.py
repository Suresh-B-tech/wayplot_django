import math
import heapq

def angle_between(a, b, c):
    ax, ay = a
    bx, by = b
    cx, cy = c

    ang1 = math.atan2(ay - by, ax - bx)
    ang2 = math.atan2(cy - by, cx - bx)

    return abs(ang1 - ang2)

def turn_a_star(graph, points, start, goal):
    pq = [(0, start, None)]  # (cost, node, parent_node)
    visited = {}
    parent = {start: None}

    while pq:
        cost, node, prev = heapq.heappop(pq)

        if node == goal:
            break

        if node in visited:
            continue
        visited[node] = cost

        for neigh in graph[node]:
            turn_cost = 0

            if prev is not None:
                turn_cost = angle_between(
                    points[prev][:2],
                    points[node][:2],
                    points[neigh][:2]
                )

            new_cost = cost + turn_cost

            if neigh not in visited or new_cost < visited.get(neigh, float('inf')):
                parent[neigh] = node
                heapq.heappush(pq, (new_cost, neigh, node))

    path = []
    cur = goal
    while cur is not None:
        path.append(cur)
        cur = parent[cur]
    return path[::-1]
