from typing import Dict, List, Tuple

graph = {
    0: [1],
    1: [0, 2],
    2: [1, 3, 7],
    3: [2, 4],
    4: [3],
    5: [6],
    6: [5, 7],
    7: [6, 8, 2],
    8: [7, 9],
    9: [8],
}

directions = {
    0: {1: "R"},
    1: {0: "L", 2: "R"},
    2: {1: "L", 3: "R", 7: "D"},
    3: {2: "L", 4: "R"},
    4: {3: "L"},
    5: {6: "R"},
    6: {5: "L", 7: "R"},
    7: {6: "L", 8: "R", 2: "U"},
    8: {7: "L", 9: "R"},
    9: {8: "L"},
}

vagas = {
    0: {"U": "A1", "D": "B1"},
    1: {"U": "A2", "D": "B2"},
    3: {"U": "A3", "D": "B3"},
    4: {"U": "A4", "D": "B4"},
    5: {"U": "C1", "D": "D1"},
    6: {"U": "C2", "D": "D2"},
    8: {"U": "C3", "D": "D3"},
    9: {"U": "C4", "D": "D4"},
}


class RobotLocationSystem:
    def __init__(self, graph: Dict[int, List[int]], directions: Dict[int, Dict[int, str]]) -> None:
        "Takes in a graph and its respective directions"
        self.graph = graph
        self.directions = directions
        self.paths = self._get_all_paths(graph)

    def _bfs(self, graph: Dict[int, List[int]], start: int, end: int) -> List[int]:
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

    def _turn(self, start, end):
        print(f"\tTurning from {start} to {end}")
        if (start in ["U", "D"] and end in ["U", "D"]) or (start in ["L", "R"] and end in ["L", "R"]):
            print("\tTurn 180 degrees.")
            return "180"
        elif (start == "U" and end == "R") or (start == "R" and end == "D") or (start == "D" and end == "L") or (start == "L" and end == "U"):
            print("\    tTurn 90 degrees right.")
            return "R"
        else:
            print("\tTurn 90 degrees left.")
            return "L"

    def get_path(self, start: int, curr_face: str, end: int, end_dir: str) -> str:
        """Walks a path from start to end, finishing facing direction end_dir."""
        path = self.paths[(start, end)]
        operations = []
        # if len(path) < 2:
        # print("No path found")
        for i in range(len(path) - 1):
            if curr_face != directions[path[i]][path[i + 1]]:
                operations.append(self._turn(curr_face, directions[path[i]][path[i + 1]]))
                curr_face = directions[path[i]][path[i + 1]]
            print(f"Moving from spot {path[i]} to spot {path[i+1]}")
            operations.append("go")
        if curr_face != end_dir:
            operations.append(self._turn(curr_face, end_dir))
            curr_face = end_dir
        return curr_face, operations

    def _get_all_paths(self, graph: Dict[int, List[int]]) -> Dict[Tuple[int, int], List[int]]:
        """Returns a Dict with all paths between every pair of nodes"""
        paths: Dict[Tuple[int, int], List[int]] = {}
        for start_node in graph:
            for end_node in graph:
                paths[(start_node, end_node)] = self._bfs(graph, start_node, end_node)
        return paths

    def get_distance_between_nodes(self, trajectory: tuple):
        start, end = trajectory
        return len(self.paths[(start, end)])


if __name__ == "__main__":
    # start position
    face = "R"
    spot = 6
    # esses valores virão do ultrasonico das vagas
    end = 0
    end_dir = "R"
    rls = RobotLocationSystem(graph, directions)
    print(f"Initial spot = {spot}, destination = {end}, direction = {end_dir}")
    face, operations = rls.get_path(spot, face, end, end_dir)
    print(operations)
    thing = [(8, 6), (0, 6), (6, 8), (2, 4)]
    thing.sort(key=rls.get_distance_between_nodes)
    print(thing)
