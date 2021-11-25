# coding=utf-8

from time import sleep, time
from datetime import datetime
import math
import json
import numpy as np
import pigpio
from threading import Thread

import requests


from grafo_busca.grafo_busca import RobotLocationSystem, graph, directions, vagas
from robot_network.notification_listener import RobotNotificationListener
from queue import Queue

from rasp_camera_detection_v4 import setup, get_plate_string

try:
    from TCS3200 import *
    from MPU6050 import *
except ModuleNotFoundError:
    print("Módulos do RPi não encontrados. Prosseguindo.")

TESTING_PLATE_RECOGNITION = True
PLATE_SERVER_URL = "https://easy-park-iw.herokuapp.com/user/linkUserToSpot"
BEGIN_SESSION_URL = "https://easy-park-iw.herokuapp.com/user/beginSession"

# pigpio documentation
# http://abyz.me.uk/rpi/pigpio/python.html


class coneBot(Thread):
    def __init__(self):
        pass

    def run(self):

        while True:
            while True:
                message = self.pspot_queue.get()
                print(f"Received message {message} from notification server.")
                # this assumes that message is just a string containing the name of a parking spot, like "A1"
                message_node = self.get_node_from_spot(message)
                message_dir = self.get_dir_from_spot(message)
                self.pspot_list.append((message_node, message_dir))
                if self.pspot_queue.empty():
                    break

            next_node, next_face = self.get_next_serviced_spot()
            print(f"Going to {next_node}, {next_face}")
            self.move_on_parking_lot_from_message(next_node, next_face)

            # self.moveOnParkingLot()
            # break  # This is here just for testing purposes


    def followLine(self):
        tcrt_read = self.tcrt.read()

        while self.ultra.measure_distance() < 10.0:  # Se entrar algo na frente, espera (pooling)
            self.motor.brake()
            sleep(0.16)

        if tcrt_read == [1, 1, 0, 1, 1]:
            self.motor.setVelLeft(1)
            self.motor.setVelRight(0.98)
            self.motor.go()

        elif tcrt_read == [1, 0, 0, 1, 1] or tcrt_read == [1, 0, 1, 1, 1]:
            self.motor.setVelLeft(1)
            self.motor.setVelRight(0.8)
            self.motor.go()

        elif tcrt_read == [0, 0, 1, 1, 1] or tcrt_read == [0, 1, 1, 1, 1]:
            self.motor.turnLeft()

        elif tcrt_read == [1, 1, 0, 0, 1] or tcrt_read == [1, 1, 1, 0, 1]:
            self.motor.setVelLeft(0.8)
            self.motor.setVelRight(1)
            self.motor.go()

        elif tcrt_read == [1, 1, 1, 0, 0] or tcrt_read == [1, 1, 1, 1, 0]:
            self.motor.turnRight()

        else:
            self.motor.setVelLeft(1)
            self.motor.setVelRight(0.98)
            self.motor.go()

    def turn(self, direction):

        self.motor.setVelLeft(1)
        self.motor.setVelRight(1)

        # manda o robo fazer a curva
        if direction == "L":
            self.motor.turnLeftSpike()
            # self.motor.turnLeft()
        else:
            self.motor.turnRightSpike()
            # self.motor.turnRight()

        ti = time.time()
        tf = time.time()

        while (tf - ti) < 0.6:
            tf = time.time()

        while not self.tcrt_side.read():  # Enquanto black
            pass

        while self.tcrt_side.read():  # Enquanto white
            pass

        self.motor.brake()

    def moveStraight(self):
        ti = time.time()
        tf = time.time()

        while (tf - ti) < 0.6:
            tf = time.time()
            self.followLine()

        while not self.tcrt_side.read():  # Enquanto black
            self.followLine()

        self.motor.setVelLeft(1)
        self.motor.setVelRight(1)

        while self.tcrt_side.read():  # Enquanto white
            self.followLine()

        self.motor.brake()

        self.motor.setVelLeft(1)  # preciso resetar, pq o followLine altera as velocidades dos motores
        self.motor.setVelRight(1)  # conforme necessidade, ai pode ter acabado o while com velocidades diferentes que 1

        self.motor.goBack()
        sleep(0.09)
        self.motor.brake()

    def moveOnParkingLot(self):
        self.motor.stop()
        sleep(13)
        face = "R"
        spot = 6

        end = 1
        end_dir = "R"

        while True:
            face, operations = self.location_system.get_path(spot, face, end, end_dir)
            print(operations)  # se quiser ver o trajeto retornado

            print("--------- ROBOT ON ---------")
            for action in operations:
                sleep(2)
                if action in ["R", "L"]:
                    print("Turning " + action)
                    self.turn(action)
                elif action in ["180"]:
                    print("Turning " + "R")
                    self.turn(action)
                    print("Turning " + "R")
                    self.turn(action)
                else:
                    print("Move straight")
                    self.moveStraight()

            print("--------- FINISH ---------")

            print("Getting foto! smile :)")
            sleep(4)

            spot = end
            face = end_dir

            end = 5
            end_dir = "D"

    def move_on_parking_lot_from_message(self, destination_node: int, destination_face: str):
        """Not-hardcoded version of moveOnParkingLot"""
        self.motor.stop()
        sleep(20)

        face, operations = self.location_system.get_path(self.node_pos, self.face, destination_node, destination_face)
        print(f"Operations needed to get to destination: {operations}")

        print("--------- ROBOT ON ---------")
        for action in operations:
            sleep(2.5)
            if action in ["R", "L"]:
                print("Turning " + action)
                sleep(2)
                # self.turn(action)
            elif action in ["180"]:
                print("Turning " + "R")
                sleep(2)
                # self.turn(action)
                print("Turning " + "R")
                sleep(2)
                # self.turn(action)
            else:
                print("Move straight")
                sleep(2)
                # self.moveStraight()
        print("Getting foto! smile :)")
        self.node_pos = destination_node
        self.face = destination_face
        self.vaga = vagas[self.node_pos][self.face]
        if TESTING_PLATE_RECOGNITION:
            self.send_plate_info_to_server()

        print("--------- FINISH ---------")

    def get_node_from_spot(self, destination_spot: str) -> int:
        for key, value in vagas.items():
            if destination_spot in value.values():
                return key
        raise Exception("Em get_node_from_spot: Vaga não encontrada no grafo.")

    def get_dir_from_spot(self, destination_spot: str) -> str:
        for key, value in vagas.items():
            for inner_key, inner_value in value.items():
                if inner_value == destination_spot:
                    return inner_key
        raise Exception("Em get_dir_from_spot: Vaga não encontrada no grafo.")

    def send_plate_info_to_server(self):
        if TESTING_PLATE_RECOGNITION:
            plate_string = get_plate_string(self.model, self.labels)
            requests.post(PLATE_SERVER_URL, json={"plate": plate_string, "spot": self.vaga})
        else:
            print("Não estamos testando reconhecimento de placas agora.")

    def get_next_serviced_spot(self):
        distance = np.infty
        for spot_node, face in self.pspot_list:
            next_dist = self.location_system.get_distance_between_nodes((self.node_pos, spot_node))
            if distance > next_dist:
                distance = next_dist
                spot_node_ret, face_ret = spot_node, face
        self.pspot_list.remove((spot_node_ret, face_ret))
        return spot_node_ret, face_ret


if __name__ == "__main__":
    c = coneBot()
    c.start()
