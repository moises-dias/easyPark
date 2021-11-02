import socket
import threading
from typing import List

PORT = 6789
SERVER = ""
ADDR = (SERVER, PORT)


class RobotNotificationListener:
    def __init__(self) -> None:
        self.pspot_list = []

    def _process_data(self) -> None:
        print(f"New connection established.")
        data = self.conn.recv(1024).decode("utf-8")
        self.pspot_list.append(data)
        self.conn.close()

    def __call__(self) -> None:
        print(f"New connection in notif. server from {self.addr}")
        self._process_data()
        print(f"Notif. server disconnected from {self.addr}")

    def get_parkspot_list(self) -> List[str]:
        return self.pspot_list

    def listen(self) -> None:
        """Starts the robot's parking spot notification listener."""
        print("Starting robot's notification listener.")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind(ADDR)
            server.listen()
            print(f"Notification server is listening")
            while True:
                self.conn, self.addr = server.accept()
                thread = threading.Thread(target=RobotNotificationListener())
                thread.start()


if __name__ == "__main__":
    rnl = RobotNotificationListener()
    rnl.listen()
