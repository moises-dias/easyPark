# coding=utf-8

from time import sleep, time
from datetime import datetime
import math
import json
import numpy as np
import pigpio
from threading import Thread

# from grafo_busca_v0 import get_path

from grafo_busca.grafo_busca import RobotLocationSystem, graph, directions, vagas
from robot_network.notification_listener import RobotNotificationListener
from queue import Queue

try:
    from TCS3200 import *
    from MPU6050 import *
except ModuleNotFoundError:
    print("Módulos do RPi não encontrados. Prosseguindo.")

# pigpio documentation
# http://abyz.me.uk/rpi/pigpio/python.html


class Motor:
    """IN1     IN2 | Motor right (top view with front facing up)
    IN3     IN4 | Motor left
    ------------------------------------
    255     0   | ahead
    0       255 | back
    0       0   | idle
    255     255 | brake
    """

    def __init__(self, rpi, IN1, IN2, IN3, IN4):
        self.input = [-1, IN1, IN2, IN3, IN4]  # do not use self.input[0]
        self.rpi = rpi
        self.vel_r = 1  # it ranges from 0 to 1
        self.vel_l = 1
        self.vel_max = 0.4
        self.dir = "stop"
        self.stop()  # garantir, vai q pino começa em high sei la

    def go(self):

        # self.spike('go')
        self.rpi.set_PWM_dutycycle(self.input[1], 0)
        self.rpi.set_PWM_dutycycle(self.input[2], 255 * self.vel_l * self.vel_max)
        self.rpi.set_PWM_dutycycle(self.input[3], 255 * self.vel_r * self.vel_max)
        self.rpi.set_PWM_dutycycle(self.input[4], 0)

    def turnLeft(self):
        # self.spike('left')
        self.rpi.set_PWM_dutycycle(self.input[1], 255 * self.vel_l * 0.74 * self.vel_max)
        self.rpi.set_PWM_dutycycle(self.input[2], 0)
        self.rpi.set_PWM_dutycycle(self.input[3], 255 * self.vel_r * 0.74 * self.vel_max)
        self.rpi.set_PWM_dutycycle(self.input[4], 0)

    def turnRight(self):
        # self.spike('right')
        self.rpi.set_PWM_dutycycle(self.input[1], 0)
        self.rpi.set_PWM_dutycycle(self.input[2], 255 * self.vel_l * 0.74 * self.vel_max)
        self.rpi.set_PWM_dutycycle(self.input[3], 0)
        self.rpi.set_PWM_dutycycle(self.input[4], 255 * self.vel_r * 0.74 * self.vel_max)

    def stop(self):
        # self.spike('stop')
        self.rpi.set_PWM_dutycycle(self.input[1], 0)
        self.rpi.set_PWM_dutycycle(self.input[2], 0)
        self.rpi.set_PWM_dutycycle(self.input[3], 0)
        self.rpi.set_PWM_dutycycle(self.input[4], 0)

    def brake(self):
        # self.spike('brake')
        self.rpi.set_PWM_dutycycle(self.input[1], 255 * self.vel_l * self.vel_max)
        self.rpi.set_PWM_dutycycle(self.input[2], 255 * self.vel_l * self.vel_max)
        self.rpi.set_PWM_dutycycle(self.input[3], 255 * self.vel_r * self.vel_max)
        self.rpi.set_PWM_dutycycle(self.input[4], 255 * self.vel_r * self.vel_max)

    def goBack(self):
        # self.spike('back')
        self.rpi.set_PWM_dutycycle(self.input[1], 255 * self.vel_l * self.vel_max)
        self.rpi.set_PWM_dutycycle(self.input[2], 0)
        self.rpi.set_PWM_dutycycle(self.input[3], 0)
        self.rpi.set_PWM_dutycycle(self.input[4], 255 * self.vel_r * self.vel_max)

    def spike(self, dir_now):
        if self.dir != dir_now:
            if dir_now == "left" or dir_now == "back":
                self.rpi.set_PWM_dutycycle(self.input[1], 255 * 0.8)
            if dir_now == "go" or dir_now == "right":
                self.rpi.set_PWM_dutycycle(self.input[2], 255 * 0.8)
            if dir_now == "go" or dir_now == "left":
                self.rpi.set_PWM_dutycycle(self.input[3], 255 * 0.8)
            if dir_now == "right" or dir_now == "back":
                self.rpi.set_PWM_dutycycle(self.input[4], 255 * 0.8)
            self.dir = dir_now
            sleep(0.070)

    def turnLeftSpike(self):
        self.rpi.set_PWM_dutycycle(self.input[1], 255 * 0.7)
        self.rpi.set_PWM_dutycycle(self.input[2], 0)
        self.rpi.set_PWM_dutycycle(self.input[3], 255 * 0.7)
        self.rpi.set_PWM_dutycycle(self.input[4], 0)
        sleep(0.07)
        self.rpi.set_PWM_dutycycle(self.input[1], 255 * self.vel_l * 0.7 * self.vel_max)
        self.rpi.set_PWM_dutycycle(self.input[2], 0)
        self.rpi.set_PWM_dutycycle(self.input[3], 255 * self.vel_r * 0.7 * self.vel_max)
        self.rpi.set_PWM_dutycycle(self.input[4], 0)

    def turnRightSpike(self):
        # self.spike('right')
        self.rpi.set_PWM_dutycycle(self.input[1], 0)
        self.rpi.set_PWM_dutycycle(self.input[2], 255 * 0.7)
        self.rpi.set_PWM_dutycycle(self.input[3], 0)
        self.rpi.set_PWM_dutycycle(self.input[4], 255 * 0.7)
        sleep(0.07)
        self.rpi.set_PWM_dutycycle(self.input[1], 0)
        self.rpi.set_PWM_dutycycle(self.input[2], 255 * self.vel_l * 0.7 * self.vel_max)
        self.rpi.set_PWM_dutycycle(self.input[3], 0)
        self.rpi.set_PWM_dutycycle(self.input[4], 255 * self.vel_r * 0.7 * self.vel_max)

    def setVelLeft(self, vel):
        if vel > 1:
            vel = 1
        elif vel < 0:
            vel = 0
        self.vel_l = vel

    def setVelRight(self, vel):
        if vel > 1:
            vel = 1
        elif vel < 0:
            vel = 0
        self.vel_r = vel

    def setVelMax(self, vel):
        if vel > 1:
            vel = 1
        elif vel < 0:
            vel = 0
        self.vel_max = vel


class Tcrt50005Channel:
    # https://thepihut.com/blogs/raspberry-pi-tutorials/how-to-use-the-tcrt5000-ir-line-follower-sensor-with-the-raspberry-pi
    # código baseado no tutorial acima
    def __init__(self, rpi, s1, s2, s3, s4, s5):
        self.sensors = [s1, s2, s3, s4, s5]
        self.rpi = rpi
        for i in self.sensors[:]:
            self.rpi.set_mode(i, pigpio.INPUT)

    def read(self):
        sensor_values = []
        for s in self.sensors[:]:
            sensor_values.append(self.rpi.read(s))
        return sensor_values


class Tcrt50001Channel:
    def __init__(self, rpi, digital, analog=None):
        self.sensors = digital
        self.rpi = rpi
        
        self.rpi.set_mode(self.sensors, pigpio.INPUT)

    def read(self):

        return 0 if self.rpi.read(self.sensors) == 1 else 1


class Ultrasonic:
    # https://tutorials-raspberrypi.com/raspberry-pi-ultrasonic-sensor-hc-sr04/
    # código baseado no tutorial acima
    def __init__(self, rpi, trig, echo):
        self.trig = trig
        self.echo = echo
        self.rpi = rpi

        self.rpi.set_mode(trig, pigpio.OUTPUT)
        self.rpi.set_mode(echo, pigpio.INPUT)

    def measure_distance(self):
        # set Trigger to HIGH
        self.rpi.write(self.trig, 1)

        # set Trigger after 0.01ms to LOW
        sleep(0.00001)
        self.rpi.write(self.trig, 0)

        StartTime = time.time()
        StopTime = time.time()

        # talvez se eu não apontar para uma parede não vai sair do while abaixo

        # save StartTime
        while not self.rpi.read(self.echo):
            StartTime = time.time()

        # save time of arrival
        while self.rpi.read(self.echo):
            StopTime = time.time()

        # time difference between start and arrival
        TimeElapsed = StopTime - StartTime
        # multiply with the sonic speed (34300 cm/s)
        # and divide by 2, because there and back
        distance = (TimeElapsed * 34300) / 2

        return distance


class coneBot(Thread):
    def __init__(self, *args, **kwargs):
        # Acho que vou criar uma classe para cada componente
        # Assim fica mais fácil setar, contorlar e ler coisas dos componentes

        # self.led = 12

        super(coneBot, self).__init__(*args, **kwargs)
        self.pspot_queue = Queue()
        self.pspot_list: list[tuple(int, str)] = []  # int is for node id, str is for direction

        self.buz = 9

        self.rpi = pigpio.pi()

        # RPi pins for [IN1, IN2, IN3, IN4] motor driver
        self.motor = Motor(self.rpi, 13, 16, 20, 21)  

        # RPi pins for [S1, S2, S3, S4, S5] tcrt5000 module
        self.tcrt = Tcrt50005Channel(self.rpi, 4, 18, 17, 27, 23)  

        # RPi pins for 
        self.tcrt_side = Tcrt50001Channel(self.rpi, 11)

        # RPi pins for OUT, S2, S3, S0, S1
        #self.color = ColorSensor(self.rpi, 6, 12, 5, 11, 7)  

        self.ultra = Ultrasonic(self.rpi, 24, 10)  # RPi pins for trig and echo
        self.gyro = Gyroscope(self.rpi)

        self.location_system = RobotLocationSystem(graph, directions)
        self.node_pos = 6  # Depois isso vai virar uma string tipo "A1"
        self.face = "R"

        self.motor.stop()
        # except Exception:
        #    print(f"You're not using a RPi. Continuing.")
        self.start_bot()

    def run(self):
        dispatcher_thread.register_interest(self)
        # robot initialization logic goes here
        # self.start_bot()

        while True:
            # while True:
            #     message = self.pspot_queue.get()
            #     print(f"Received message {message} from notification server.")
            #     # this assumes that message is just a string containing the name of a parking spot, like "A1"
            #     message_node = self.get_node_from_spot(message)
            #     message_dir = self.get_dir_from_spot(message)
            #     self.pspot_list.append((message_node, message_dir))
            #     if self.pspot_queue.empty():
            #         break

            #next_node, next_face = self.get_next_serviced_spot()
            #print(f"Going to {next_node}, {next_face}")
            #self.move_on_parking_lot_from_message(next_node, next_face)

            self.moveOnParkingLot()
            # break  # This is here just for testing purposes

    def put_message(self, message):
        self.pspot_queue.put(message)

    def start_bot(self):

        self.motor.setVelMax(0.33)

        # self.color.set_update_interval(0.07)
        # calibrate_colors = False
        # if calibrate_colors:
        #     input("Calibrating black object, press RETURN to start")
        #     hz = self.color.get_hertz()
        #     print(hz)
        #     self.color.set_black_level(hz)

        #     input("Calibrating white object, press RETURN to start")
        #     hz = self.color.get_hertz()
        #     print(hz)
        #     self.color.set_white_level(hz)
        # else:
        #     self.color.set_black_level([129, 132, 169])
        #     # self.color.set_black_level([239, 239, 314])
        #     self.color.set_white_level([1727, 1775, 2297])
        #     # self.color.set_white_level([1523, 1576, 2041])

        # fazer um while ultrasonico detectou fica parado
        # ler o sensor de cor e saber onde eu estou, guardar o status (localização)


    def test_led(self):
        flag = True
        while 1:
            self.rpi.write(self.led, flag)
            flag = not flag
            sleep(1)

    def test_buzzer(self):
        i = 0
        self.rpi.set_PWM_dutycycle(self.buz, 128)  #  50 %
        while 1:
            i = 800
            self.rpi.set_PWM_frequency(self.buz, i)
            sleep(0.3)
            i = 1500
            self.rpi.set_PWM_frequency(self.buz, i)
            sleep(0.3)

    def test_ultrassom(self):
        while 1:
            print(self.ultra.measure_distance())
            sleep(0.1)

    def test_gyro(self):
        while 1:
            print(
                np.round(list(self.gyro.read_gyro()), 4),
                np.round(list(self.gyro.read_acc()), 4),
            )
            sleep(0.05)

    def followLine(self):
        # podemos criar métodos para virar proporcionalmente dependendo do output do tcrt
        # pelo que eu entendi:
        # 1 = motor r frente
        # 2 = motor r trás
        # 3 = motor l frente
        # 4 = motor l trás
        # tcrt é uma lista de bool com 5 itens, referentes a leitura do tcrt
        # indo da esquerda para a direita
        sleep(13)
        while 1:
            tcrt_read = self.tcrt.read()

            if tcrt_read == [1, 1, 0, 1, 1]:
                print("1, 1")
                self.motor.setVelLeft(1)
                self.motor.setVelRight(1)

            if tcrt_read == [1, 0, 1, 1, 1]:
                print("0.7, 1")
                self.motor.setVelLeft(0.7)
                self.motor.setVelRight(1)

            if tcrt_read == [1, 1, 1, 0, 1]:
                print("1, 0.7")
                self.motor.setVelLeft(1)
                self.motor.setVelRight(0.7)

            if tcrt_read == [0, 1, 1, 1, 1]:
                print("0.4, 1")
                self.motor.setVelLeft(0.4)
                self.motor.setVelRight(1)

            if tcrt_read == [1, 1, 1, 1, 0]:
                print("1, 0.4")
                self.motor.setVelLeft(1)
                self.motor.setVelRight(0.4)

            self.motor.go()

        # podemos dar um break/stop se não identificar nada, podemos testar isso

    # as próximas funções (followLineDumbSemWhileTrue, turn, moveStraight e moveOnParkingLot) são referentes a movimentação no estacionamento

    def followLineDumbSemWhileTrue(self):
        tcrt_read = self.tcrt.read()

        if tcrt_read == [1, 1, 0, 1, 1] :
            self.motor.setVelLeft(1)
            self.motor.setVelRight(1)
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

        # elif any([not i for i in tcrt_read[0:1]]) and any(
        #    [not i for i in tcrt_read[4:5]]):  # detectou sensor dos dois lados, tcrt deve ta em cima da interseção, manda reto
        else:
            self.motor.setVelLeft(1)
            self.motor.setVelRight(1)
            self.motor.go()

    def turn(self, direction):
        read_samples = 1  # colocar isso la no começo, n fiz isso pq podemos mudar
        threshold = 125  # limite para considerar uma cor como preto ou não

        # manda o robo fazer a curva
        if direction == "L":
            self.motor.turnLeftSpike()
            # self.motor.turnLeft()
        else:
            self.motor.turnRightSpike()
            # self.motor.turnRight()

        readings = [1] * read_samples
        # readings são as leituras para saber se eu estou ou não na faixa, inicia em 1 pq o sensor de cor ta na faixa inicialmente
        # podemos fazer com 5, 10, qnts leituras for melhor

        while any(readings):  # enquanto eu estiver vendo a faixa
            rgb_values = self.color.get_rgb()
            readings.append(int(all(color < threshold for color in rgb_values)))  # se o R, G e B for menor que threshold = preto
            readings = readings[-read_samples:]
        # se saiu do while é pq as ultimas 'samples' leituras NAO identificaram preto
        # agr vamo tentar achar uma faixa dvolta

        while not all(readings):  # enqnt as ultimas leituras nao acharam a faixa
            rgb_values = self.color.get_rgb()
            readings.append(int(all(color < threshold for color in rgb_values)))
            readings = readings[-read_samples:]
        # se saiu do while é pq as ultimas 'samples' leituras identificaram preto

        # if direction == "L":
        #     self.motor.turnRightSpike()
        # else:
        #     self.motor.turnLeftSpike()
        # sleep(0.08)
        self.motor.brake()

    def moveStraight(self):
        read_samples = 1
        threshold = 125
        readings = [1] * read_samples
        while any(readings):
            self.followLineDumbSemWhileTrue()
            rgb_values = self.color.get_rgb()
            readings.append(int(all(color < threshold for color in rgb_values)))
            readings = readings[-read_samples:]

        self.motor.setVelLeft(1)  # preciso resetar, pq de vez em quando ele chega de revesgueio
        self.motor.setVelRight(1)  # com um dos motores em velocidade menor

        while not all(readings):
            self.followLineDumbSemWhileTrue()
            rgb_values = self.color.get_rgb()
            readings.append(int(all(color < threshold for color in rgb_values)))
            readings = readings[-read_samples:]

        self.motor.setVelLeft(1)  # preciso resetar, pq de vez em quando ele chega de revesgueio
        self.motor.setVelRight(1)  # com um dos motores em velocidade menor

        # self.motor.goBack()
        # sleep(0.08)
        self.motor.brake()

    def turn_2(self, direction):

        self.motor.setVelLeft(1)  # preciso resetar, pq de vez em quando ele chega de revesgueio
        self.motor.setVelRight(1)  # com um dos motores em velocidade menor

        # manda o robo fazer a curva
        if direction == "L":
            self.motor.turnLeftSpike()
            # self.motor.turnLeft()
        else:
            self.motor.turnRightSpike()
            # self.motor.turnRight()
        
        ti = time.time()
        tf = time.time()

        while not self.tcrt_side.read() and (tf - ti) < 1.5:  # enquanto black
            pass

        while self.tcrt_side.read() and (tf - ti) < 1.5:  # enquanto white
            pass

        self.motor.brake()
        sleep(0.08)
        if direction == "L":
            self.motor.turnRightSpike()
        else:
            self.motor.turnLeftSpike()
        sleep(0.08)
        self.motor.brake()

    def moveStraight_2(self):
        while not self.tcrt_side.read():    # Enquanto black
            self.followLineDumbSemWhileTrue()

        self.motor.setVelLeft(1)  # preciso resetar, pq de vez em quando ele chega de revesgueio
        self.motor.setVelRight(1)  # com um dos motores em velocidade menor

        while self.tcrt_side.read():    # Enquanto white
            self.followLineDumbSemWhileTrue()

        
        self.motor.brake()
        sleep(0.08)
        self.motor.goBack()
        sleep(0.08)
        self.motor.brake()


        self.motor.setVelLeft(1)  # preciso resetar, pq de vez em quando ele chega de revesgueio
        self.motor.setVelRight(1)  # com um dos motores em velocidade menor

    def moveOnParkingLot(self):
        self.motor.stop()
        sleep(13)
        face = "R"
        spot = 6

        end = 1
        end_dir = "R"


        face, operations = self.location_system.get_path(spot, face, end, end_dir)
        print(operations)  # se quiser ver o trajeto retornado

        print("--------- ROBOT ON ---------")
        for action in operations:
            sleep(2)
            if action in ["R", "L"]:
                print("Turning " + action)
                self.turn_2(action)
            elif action in ["180"]:
                print("Turning " + "R")
                self.turn_2(action)
                print("Turning " + "R")
                self.turn_2(action)
            else:
                print("Move straight")
                self.moveStraight_2()

        print("--------- FINISH ---------")

        # tira foto

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
                #self.turn(action)
            elif action in ["180"]:
                print("Turning " + "R")
                sleep(2)
                #self.turn(action)
                print("Turning " + "R")
                sleep(2)
                #self.turn(action)
            else:
                print("Move straight")
                sleep(2)
                #self.moveStraight()
        print("Getting foto! smile :)")
        self.send_plate_info_to_server()

        self.node_pos = destination_node
        self.face = destination_face
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
        pass

    def get_next_serviced_spot(self):  # -> tuple[int, str]:
        distance = np.infty
        for spot_node, face in self.pspot_list:
            next_dist = self.location_system.get_distance_between_nodes((self.node_pos, spot_node))
            if distance > next_dist:
                distance = next_dist
                spot_node_ret, face_ret = spot_node, face
        self.pspot_list.remove((spot_node_ret, face_ret))
        return spot_node_ret, face_ret


if __name__ == "__main__":
    dispatcher_thread = RobotNotificationListener()
    dispatcher_thread.start()

    c = coneBot()
    c.start()

    dispatcher_thread.join()

