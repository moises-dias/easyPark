import socket
import threading

PORT = 6789
SERVER = ""
ADDR = (SERVER, PORT)


class RobotPSpotDataHandler:

    def __init__(self, conn: socket.socket, addr) -> None:
        self.conn = conn
        self.addr = addr
        self.pspot_list = []
    
    def process_data(self):
        print(f"New connection established.")
        data = self.conn.recv(1024).decode("utf-8")
        self.pspot_list.append(data)
        self.conn.close()
    
    def __call__(self) -> None:
        print(f"New connection from {self.addr}")
        self.process_data()
        print(f"Disconnected from {self.addr}")

if __name__ == "__main__":
    print("Starting server!")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind(ADDR)
        server.listen()
        print(f"Server is listening")
        while True:
            conn, addr = server.accept()
            thread = threading.Thread(target=RobotPSpotDataHandler(conn, addr))
            thread.start()