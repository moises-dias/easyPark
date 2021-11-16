# coding=utf-8

from time import sleep, time
import math
import json
import numpy as np
import pigpio
from threading import Thread

# from grafo_busca_v0 import get_path

from grafo_busca.grafo_busca import RobotLocationSystem, graph, directions
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
        self.stop()  # garantir, vai q pino começa em high sei la

    def go(self):
        self.rpi.set_PWM_dutycycle(self.input[1], 0)
        self.rpi.set_PWM_dutycycle(self.input[2], 255 * self.vel_l * self.vel_max)
        self.rpi.set_PWM_dutycycle(self.input[3], 255 * self.vel_r * self.vel_max)
        self.rpi.set_PWM_dutycycle(self.input[4], 0)

    def turnLeft(self):
        self.rpi.set_PWM_dutycycle(
            self.input[1], 255 * self.vel_l * 0.74 * self.vel_max
        )
        self.rpi.set_PWM_dutycycle(self.input[2], 0)
        self.rpi.set_PWM_dutycycle(
            self.input[3], 255 * self.vel_r * 0.74 * self.vel_max
        )
        self.rpi.set_PWM_dutycycle(self.input[4], 0)

    def turnRight(self):
        self.rpi.set_PWM_dutycycle(self.input[1], 0)
        self.rpi.set_PWM_dutycycle(
            self.input[2], 255 * self.vel_l * 0.74 * self.vel_max
        )
        self.rpi.set_PWM_dutycycle(self.input[3], 0)
        self.rpi.set_PWM_dutycycle(
            self.input[4], 255 * self.vel_r * 0.74 * self.vel_max
        )

    def stop(self):
        self.rpi.set_PWM_dutycycle(self.input[1], 0)
        self.rpi.set_PWM_dutycycle(self.input[2], 0)
        self.rpi.set_PWM_dutycycle(self.input[3], 0)
        self.rpi.set_PWM_dutycycle(self.input[4], 0)

    def brake(self):
        self.rpi.set_PWM_dutycycle(self.input[1], 255 * self.vel_l * self.vel_max)
        self.rpi.set_PWM_dutycycle(self.input[2], 255 * self.vel_l * self.vel_max)
        self.rpi.set_PWM_dutycycle(self.input[3], 255 * self.vel_r * self.vel_max)
        self.rpi.set_PWM_dutycycle(self.input[4], 255 * self.vel_r * self.vel_max)

    def goBack(self):
        self.rpi.set_PWM_dutycycle(self.input[1], 255 * self.vel_l * self.vel_max)
        self.rpi.set_PWM_dutycycle(self.input[2], 0)
        self.rpi.set_PWM_dutycycle(self.input[3], 0)
        self.rpi.set_PWM_dutycycle(self.input[4], 255 * self.vel_r * self.vel_max)

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


class Tcrt5000:
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
        self.pspot_list: list[
            tuple(int, str)
        ] = []  # int is for node id, str is for direction

        self.buz = 9

        self.rpi = pigpio.pi()

        self.motor = Motor(
            self.rpi, 13, 16, 20, 21
        )  # RPi pins for [IN1, IN2, IN3, IN4] motor driver
        self.motor.setVelMax(0.45)

        self.tcrt = Tcrt5000(
            self.rpi, 4, 18, 17, 27, 23
        )  # RPi pins for [S1, S2, S3, S4, S5] tcrt5000 module
        self.color = ColorSensor(
            self.rpi,
            6,
            12,
            5,
            11,
            7,
        )  # RPi pins for OUT, S2, S3, S0, S1
        self.color.set_update_interval(0.1)
        self.color.set_black_level([239, 239, 314])
        self.color.set_white_level([1523, 1576, 2041])

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
            #message = self.pspot_queue.get()
            #print(f"Received message {message} from notification server.")
            # this assumes that message is just a string containing the name of a parking spot, like "A1"
            # TODO: build a mapping between nodes and spots, remembering to include direction.
            #message_node = self.get_node_from_spot(message)
            #message_dir = self.get_dir_from_spot(message)

            #self.pspot_list.append((message_node, message_dir))

            #next_node, next_face = self.get_next_serviced_spot()
            #self.move_on_parking_lot_from_message(next_node, next_face)

            self.moveOnParkingLot()
            break  # This is here just for testing purposes

    def put_message(self, message):
        self.pspot_queue.put(message)

    def start_bot(self):

        calibrate_colors = False
        if calibrate_colors:
            input("Calibrating black object, press RETURN to start")
            hz = self.color.get_hertz()
            print(hz)
            self.color.set_black_level(hz)

            input("Calibrating white object, press RETURN to start")
            hz = self.color.get_hertz()
            print(hz)
            self.color.set_white_level(hz)
        else:
            self.color.set_black_level([129, 132, 169])
            self.color.set_white_level([1727, 1775, 2297])

        # fazer um while ultrasonico detectou fica parado
        # ler o sensor de cor e saber onde eu estou, guardar o status (localização)

    def test_motor(self):
        sleep(5)
        self.motor.setVelMax(0.4)
        while 1:
            print("\ngo")
            self.motor.go()
            sleep(3)
            print("\n--- stop ---\n")
            self.motor.stop()
            sleep(3)

            print("\nturn left")
            self.motor.turnLeft()
            sleep(3)
            print("\n--- stop ---\n")
            self.motor.stop()
            sleep(3)

            print("\nturn right")
            self.motor.turnRight()
            sleep(3)
            print("\n--- stop ---\n")
            self.motor.stop()
            sleep(3)

            print("\nback")
            self.motor.goBack()
            sleep(3)
            print("\n--- stop ---\n")
            self.motor.stop()
            sleep(10)

    def test_tcrt(self):
        while 1:
            print(self.tcrt.read())

    def test_color(self):

        self.color.set_update_interval(0.1)

        input("Calibrating black object, press RETURN to start")
        hz = self.color.get_hertz()
        # hz = [239, 239, 314]
        print(hz)
        self.color.set_black_level([239, 239, 314])

        input("Calibrating white object, press RETURN to start")
        hz = self.color.get_hertz()
        # hz = [1523, 1576, 2041]
        print(hz)
        self.color.set_white_level([1523, 1576, 2041])

        while 1:
            print(np.round(list(self.color.get_rgb()), 4), self.color.color())

        self.color.cancel()
        self.pi.stop()

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

    def followLineTest(self):
        sleep(13)

        # precisamos guardar o estado pq se ele perdeu todos os sensores vamos recorrer a isso para saber o que ele estava fazendo antes
        state = "straight"

        while 1:
            tcrt_read = self.tcrt.read()

            # estou assumindo que a posição 0 do tcrt_read seja a mais a esquerda do modulo, e a posição 4 a mais a direita

            # da forma como estava sendo feita, como você mesmo falou, nós só pegavamos essas combinações:
            # [1, 1, 0, 1, 1], [1, 0, 1, 1, 1], [1, 1, 1, 0, 1], [0, 1, 1, 1, 1], [1, 1, 1, 1, 0]
            # com esse código nós resolvemos os casos onde for detectado mais de um sensor

            if tcrt_read[0] == 0:  # se o mais a esquerda detectou linha
                state = "turning_left"

            elif (
                tcrt_read[1] == 0
            ):  # ELIF, pq se eu ja peguei o sensor da extremidade posso ignorar esse pq tenho que virar bastante
                state = "soft_turning_left"

            elif tcrt_read[4] == 0:  # se o mais a direita detectou linha
                state = "turning_right"

            elif (
                tcrt_read[3] == 0
            ):  # se o sensor entre o central e o extremo da direita (extrema direita bolsonaro kkk)
                state = "soft_turning_right"

            elif tcrt_read[2] == 0:  # se pegou APENAS o sensor central pode pisar fundo
                state = "straight"

            if state == "straight":
                print("1, 1")
                self.motor.setVelLeft(1)
                self.motor.setVelRight(1)
            elif state == "soft_turning_right":
                print("0.8, 1")
                self.motor.setVelLeft(0.8)
                self.motor.setVelRight(1)
            elif state == "turning_right":
                print("0.9, 0.4")
                self.motor.setVelLeft(
                    0.9
                )  # como a curva ta bem fechada acho interessante diminuir um pouco, pelo menos no primeiro teste
                self.motor.setVelRight(0.4)
            elif state == "soft_turning_left":
                print("1, 0.8")
                self.motor.setVelLeft(1)
                self.motor.setVelRight(0.8)
            elif state == "turning_left":
                print("0.4, 0.9")
                self.motor.setVelLeft(0.4)
                self.motor.setVelRight(
                    0.9
                )  # como a curva ta bem fechada acho interessante diminuir um pouco, pelo menos no primeiro teste

            self.motor.go()

        # podemos dar um break/stop se não identificar nada, podemos testar isso

    def followLineDumb(self):
        sleep(13)
        self.motor.go()
        while 1:
            tcrt_read = self.tcrt.read()

            if tcrt_read == [1, 1, 0, 1, 1]:
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

    # as próximas funções (followLineDumbSemWhileTrue, turn, moveStraight e moveOnParkingLot) são referentes a movimentação no estacionamento

    def followLineDumbSemWhileTrue(self):
        tcrt_read = self.tcrt.read()

        if tcrt_read == [1, 1, 0, 1, 1]:
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

        elif any(tcrt_read[0:2]) and any(
            tcrt_read[3:5]
        ):  # detectou sensor dos dois lados, tcrt deve ta em cima da interseção, manda reto
            self.motor.setVelLeft(1)
            self.motor.setVelRight(1)
            self.motor.go()

    def turn(self, direction):
        read_samples = 1  # colocar isso la no começo, n fiz isso pq podemos mudar
        threshold = 125  # limite para considerar uma cor como preto ou não

        # manda o robo fazer a curva
        if direction == "L":
            self.motor.turnLeft()
        else:
            self.motor.turnRight()

        readings = [1] * read_samples
        # readings são as leituras para saber se eu estou ou não na faixa, inicia em 1 pq o sensor de cor ta na faixa inicialmente
        # podemos fazer com 5, 10, qnts leituras for melhor

        while any(readings):  # enquanto eu estiver vendo a faixa
            rgb_values = self.color.get_rgb()  # TEM Q INSTANCIAR A CLASSE DO TCS3200
            readings.append(
                int(all(color < threshold for color in rgb_values))
            )  # se o R, G e B for menor que threshold = preto
            readings = readings[-read_samples:]
        # se saiu do while é pq as ultimas 'samples' leituras NAO identificaram preto
        # agr vamo tentar achar uma faixa dvolta

        while not all(readings):  # enqnt as ultimas leituras nao acharam a faixa
            rgb_values = self.color.get_rgb()  # TEM Q INSTANCIAR A CLASSE DO TCS3200
            readings.append(int(all(color < threshold for color in rgb_values)))
            readings = readings[-read_samples:]
        # se saiu do while é pq as ultimas 'samples' leituras identificaram preto

        self.motor.stop()  # ou brake?

    def moveStraight(self):
        read_samples = 1
        threshold = 125
        readings = [1] * read_samples
        while any(readings):
            self.followLineDumbSemWhileTrue()  # follow line
            rgb_values = self.color.get_rgb()  # TEM Q INSTANCIAR A CLASSE DO TCS3200
            readings.append(
                int(all(color < threshold for color in rgb_values))
            )  # se o R, G e B for menor que threshold = preto
            readings = readings[-read_samples:]
        while not all(readings):
            self.followLineDumbSemWhileTrue()  # follow line
            rgb_values = self.color.get_rgb()  # TEM Q INSTANCIAR A CLASSE DO TCS3200
            readings.append(
                int(all(color < threshold for color in rgb_values))
            )  # se o R, G e B for menor que threshold = preto
            readings = readings[-read_samples:]
        self.motor.stop()

    def moveOnParkingLot(self):
        self.motor.stop()
        sleep(13)
        face = "R"
        spot = 6

        end = 0
        end_dir = "R"

        face, operations = self.location_system.get_path(spot, face, end, end_dir)
        print(operations)  # se quiser ver o trajeto retornado

        # operations = ['R', 'go']

        print("--------- ROBOT ON ---------")
        for action in operations:
            sleep(2)
            if action in ["R", "L"]:
                print("Turning " + action)
                self.turn(action)
            else:
                print("Move straight")
                self.moveStraight()

        # tira foto

    def move_on_parking_lot_from_message(
        self, destination_node: int, destination_face: str
    ):
        """Not-hardcoded version of moveOnParkingLot"""
        self.motor.stop()
        sleep(20)

        face, operations = self.location_system.get_path(
            self.node_pos, self.face, destination_node, destination_face
        )
        print(f"Operations needed to get to destination: {operations}")

        print("--------- ROBOT ON ---------")
        for action in operations:
            sleep(2.5)
            if action in ["R", "L"]:
                print("Turning " + action)
                self.turn(action)
            else:
                print("Move straight")
                self.moveStraight()
        self.send_plate_info_to_server()

        self.node_pos = destination_node
        self.face = destination_face
'''
    def get_node_from_spot(self, destination_spot: str) -> int:
        return 0  # Implementar depois, vamos ter que acrescentar informação de vagas em cada nó no grafo

    def get_dir_from_spot(self, destination_spot: str) -> str:
        return "R"  # Implementar depois, vamos ter que acrescentar informação de em que direção está a vaga recebida no grafo

    def send_plate_info_to_server(self):
        pass

    def get_next_serviced_spot(self) -> tuple[int, str]:
        distance = np.infty
        for spot_node, face in self.pspot_list:
            next_dist = self.location_system.get_distance_between_nodes(
                (self.node_pos, spot_node)
            )
            if distance > next_dist:
                distance = next_dist
                spot_node_ret, face_ret = spot_node, face
        self.pspot_list.remove((spot_node_ret, face_ret))
        return spot_node_ret, face_ret
'''

if __name__ == "__main__":
    dispatcher_thread = RobotNotificationListener()
    dispatcher_thread.start()

    c = coneBot()
    c.start()

    dispatcher_thread.join()
    # c.start_bot()

    # c.start()
    # c.test_motor()    # ok
    # c.test_tcrt()     # ok
    # c.test_color()    # ok
    # c.test_buzzer()  # ok
    # c.test_ultrassom() # ok
    # c.test_gyro()     # ok
    # c.followLineDumb()
    # c.start()

    # c.moveOnParkingLot()  # para testar o movimento no estacionamento
