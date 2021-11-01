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
    elif (start == 'U' and end == 'R') or (start == 'R' and end == 'D') or (start == 'D' and end == 'L') or (start == 'L' and end == 'U'):
        print('\tTurn 90 degrees right.')
    else:
        print('\tTurn 90 degrees left.')

def walk_path(start, face, end):
    path = bfs(graph, start, end)
    if len(path) < 2:
        print('No path found')
    for i in range(len(path) - 1):
        if face != directions[path[i]][path[i+1]]:
            turn(face, directions[path[i]][path[i+1]])
            face = directions[path[i]][path[i+1]]
        print(f'Moving from spot {path[i]} to spot {path[i+1]}')
    return face

# start position
face = 'U'
spot = 6

end = 0
print(f"Initial spot = {spot}, destination = {end}")
face = walk_path(spot, face, end)








