from signalrcore.hub_connection_builder import HubConnectionBuilder
import logging
from threading import Thread
from queue import Queue
from time import sleep

SERVER_URL = "https://easy-park-iw.herokuapp.com/robotHub"


class RobotNotificationListener(Thread):
    def __init__(self, *args, **kwargs) -> None:
        super(RobotNotificationListener, self).__init__(*args, **kwargs)
        self.interested_threads = []
        self.last_message = ""

    def run(self):
        hub_connection = (
            HubConnectionBuilder()
            .with_url(SERVER_URL)
            # .configure_logging(logging.DEBUG, socket_trace=True)
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
                # hub_connection.on("CarHasParked", self.dispatch_message)
                # sleep(0.1)
                # Uncomment the lines below to test (and comment the above ones).
                hub_connection.on("Teste", self.dispatch_message)
                sleep(0.1)  # EXTREMELY IMPORTANT:
                #            this makes memory usage not blow up, and improves responsiveness
            except Exception as e:
                print(
                    f"Exception ocurred in robot's notification listener. Exiting. Exception: {e}"
                )
                break
        hub_connection.stop()

    def register_interest(self, thread):
        self.interested_threads.append(thread)

    def dispatch_message(self, message):
        if message[0] != self.last_message:
            for thread in self.interested_threads:
                self.last_message = message[0]
                thread.put_message(message[0])


class WorkerThread(Thread):
    def __init__(self, *args, **kwargs):
        super(WorkerThread, self).__init__(*args, **kwargs)
        self.pspot_queue = Queue()

    def run(self):
        dispatcher_thread.register_interest(self)

        while True:
            message = self.pspot_queue.get()
            print(f"Here's our message: {message}")

    def put_message(self, message):
        self.pspot_queue.put(message)


if __name__ == "__main__":
    dispatcher_thread = RobotNotificationListener()
    dispatcher_thread.start()

    worker_thread = WorkerThread()
    worker_thread.start()

    dispatcher_thread.join()
