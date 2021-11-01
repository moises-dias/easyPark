graph = {
    'A0' : ['A1'],
    'A1' : ['A0', 'A2'],
    'A2' : ['A1', 'A3', 'B1', 'B2'],
    'A3' : ['A2', 'A4', 'B1', 'B2'],
    'A4' : ['A3'],
    'B0' : ['B1'],
    'B1' : ['B0', 'B2', 'A2', 'A3'],
    'B2' : ['B1', 'B3', 'A2', 'A3'],
    'B3' : ['B2', 'B4'],
    'B4' : ['B3', 'B5', 'C1', 'C2'],
    'B5' : ['B4', 'C1', 'C2'],
    'C0' : ['C1'],
    'C1' : ['C0', 'C2', 'B4', 'B5'],
    'C2' : ['C1', 'C3', 'B4', 'B5'],
    'C3' : ['C2']
}

directions = {
    'A0' : {'A1': 'X'},
    'A1' : {'A0': 'X', 'A2': 'X'},
    'A2' : {'A1': 'X', 'A3': 'X', 'B1': 'X', 'B2': 'X'},
    'A3' : {'A2': 'X', 'A4': 'X', 'B1': 'X', 'B2': 'X'},
    'A4' : {'A3': 'X'},
    'B0' : {'B1': 'X'},
    'B1' : {'B0': 'X', 'B2': 'X', 'A2': 'X', 'A3': 'X'},
    'B2' : {'B1': 'X', 'B3': 'X', 'A2': 'X', 'A3': 'X'},
    'B3' : {'B2': 'X', 'B4': 'X'},
    'B4' : {'B3': 'X', 'B5': 'X', 'C1': 'X', 'C2': 'X'},
    'B5' : {'B4': 'X', 'C1': 'X', 'C2': 'X'},
    'C0' : {'C1': 'X'},
    'C1' : {'C0': 'X', 'C2': 'X', 'B4': 'X', 'B5': 'X'},
    'C2' : {'C1': 'X', 'C3': 'X', 'B4': 'X', 'B5': 'X'},
    'C3' : {'C2': 'X'}
}

def bfs(graph, start, end):
    visited = []
    paths_queue = []
    visited.append(start)
    paths_queue.append([start])

    if start == end:
        return [start]

    while paths_queue:
        path = paths_queue.pop(0) 
        
        for neighbour in graph[path[-1]]:
            if neighbour == end:
                return path + [neighbour]
            if neighbour not in visited:
                visited.append(neighbour)
                paths_queue.append(path + [neighbour])
    
    return []

# Driver Code
print(bfs(graph, 'C3', 'B0'))