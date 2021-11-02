from typing import Dict, List, Tuple

graph = {
    0: [1],
    1: [0, 8],
    2: [8],
    3: [8],
    4: [8, 5],
    5: [4, 9],
    6: [9],
    7: [9],
    8: [1, 3, 2, 4],
    9: [7, 6, 5],
}

directions = {
    0: {1: "U"},
    1: {0: "D", 8: "U"},
    2: {8: "R"},
    3: {8: "D"},
    4: {8: "L", 5: "R"},
    5: {4: "L", 9: "R"},
    6: {9: "D"},
    7: {9: "U"},
    8: {1: "D", 3: "U", 2: "L", 4: "R"},
    9: {7: "D", 6: "U", 5: "L"},
}


class RobotLocationSystem:
    def __init__(
        self, graph: Dict[int, List[int]], directions: Dict[int, Dict[int, str]]
    ) -> None:
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
        if (start in ["U", "D"] and end in ["U", "D"]) or (
            start in ["L", "R"] and end in ["L", "R"]
        ):
            print("\tTurn 180 degrees.")
        elif (
            (start == "U" and end == "R")
            or (start == "R" and end == "D")
            or (start == "D" and end == "L")
            or (start == "L" and end == "U")
        ):
            print("\tTurn 90 degrees right.")
        else:
            print("\tTurn 90 degrees left.")

    def walk_path(self, start: int, face: str, end: int, end_dir: str) -> str:
        """Walks a path from start to end, finishing facing direction end_dir. Returns the direction the robot is facing."""
        # path = self._bfs(graph, start, end)
        path = self.paths[(start, end)]
        if len(path) < 2:
            print("No path found")
        for i in range(len(path) - 1):
            if face != directions[path[i]][path[i + 1]]:
                self._turn(face, directions[path[i]][path[i + 1]])
                face = directions[path[i]][path[i + 1]]
            print(f"Moving from spot {path[i]} to spot {path[i+1]}")
        if face != end_dir:
            self._turn(face, end_dir)
            face = end_dir
        self.face = face
        return face

    def _get_all_paths(
        self, graph: Dict[int, List[int]]
    ) -> Dict[Tuple[int, int], List[int]]:
        """Returns a Dict with all paths between every pair of nodes"""
        paths: Dict[Tuple[int, int], List[int]] = {}
        for start_node in graph:
            for end_node in graph:
                paths[(start_node, end_node)] = self._bfs(graph, start_node, end_node)
        return paths


if __name__ == "__main__":
    # start position
    face = "U"
    spot = 6
    # esses valores virão do ultrasonico das vagas
    end = 0
    end_dir = "R"
    rls = RobotLocationSystem()
    print(f"Initial spot = {spot}, destination = {end}, direction = {end_dir}")
    face = rls.walk_path(spot, face, end, end_dir)
    for key, value in rls._get_all_paths(graph).items():
        print(f"Path from {key[0]} to {key[1]} : {value}")
