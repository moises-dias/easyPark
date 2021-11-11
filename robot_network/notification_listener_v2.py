from signalrcore.hub_connection_builder import HubConnectionBuilder
import logging

SERVER_URL = "https://easy-park-iw.herokuapp.com/robotHub"


class RobotNotificationListener:
    def __init__(self) -> None:
        self.pspot_list = []

    def listen(self):
        hub_connection = (
            HubConnectionBuilder()
            .with_url(SERVER_URL)
            .configure_logging(logging.DEBUG, socket_trace=True)
            .with_automatic_reconnect(
                {
                    "type": "raw",
                    "keep_alive_interval": 10,
                    "reconnect_interval": 5,
                    "max_attempts": 5,
                }
            )
            .build()
        )
        print("Starting hub connection.")
        hub_connection.start()
        print("Hub connection started.")

        while True:
            try:
                hub_connection.on("CarHasParked", self.pspot_list.append)
                # Uncomment the lines below to test.
                # hub_connection.on("Teste", self.pspot_list.append)
                # if len(self.pspot_list) > 0:
                #     print(f"\n{self.pspot_list=}\n")
                #     break
            except Exception as e:
                print(
                    f"Exception ocurred in robot's notification listener. Exiting. Exception: {e}"
                )
                break
        hub_connection.stop()


if __name__ == "__main__":
    rnl = RobotNotificationListener()
    rnl.listen()
