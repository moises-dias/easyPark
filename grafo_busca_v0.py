graph = {
    0 : [1],
    1 : [0, 8],
    2 : [8],
    3 : [8],
    4 : [8, 5],
    5 : [4, 9],
    6 : [9],
    7 : [9],
    8 : [1, 3, 2, 4],
    9 : [7, 6, 5]
}

directions = {
    0 : {1: 'U'},
    1 : {0: 'D', 8: 'U'},
    2 : {8: 'R'},
    3 : {8: 'D'},
    4 : {8: 'L', 5: 'R'},
    5 : {4: 'L', 9: 'R'},
    6 : {9: 'D'},
    7 : {9: 'U'},
    8 : {1: 'D', 3: 'U', 2: 'L', 4: 'R'},
    9 : {7: 'D', 6: 'U', 5: 'L'}
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

def turn(start, end):
    print(f'\tTurning from {start} to {end}')
    if (start in ['U', 'D'] and end in ['U', 'D']) or (start in ['L', 'R'] and end in ['L', 'R']):
        print('\tTurn 180 degrees.')
        return '180'
    elif (start == 'U' and end == 'R') or (start == 'R' and end == 'D') or (start == 'D' and end == 'L') or (start == 'L' and end == 'U'):
        print('\tTurn 90 degrees right.')
        return 'R'
    else:
        print('\tTurn 90 degrees left.')
        return 'L'

def get_path(start, face, end, end_dir):
    path = bfs(graph, start, end)
    operations = []
    if len(path) < 2:
        print('No path found')
    for i in range(len(path) - 1):
        if face != directions[path[i]][path[i+1]]:
            operations.append(turn(face, directions[path[i]][path[i+1]]))
            face = directions[path[i]][path[i+1]]
        print(f'Moving from spot {path[i]} to spot {path[i+1]}')
        operations.append('go')
    if face != end_dir:
        operations.append(turn(face, end_dir))
        face = end_dir
    return face, operations

# start position
face = 'R'
spot = 6

end = 0
end_dir = "R"
print(f"Initial spot = {spot}, destination = {end}")
face, operations = get_path(spot, face, end, end_dir)
print(operations)