def build_graph(points):
    points = points[0]
    graph = {}

    for i in range(len(points) - 1):
        graph.setdefault(i, []).append(i + 1)
        graph.setdefault(i + 1, []).append(i)

    return graph
