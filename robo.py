# coding=utf-8

from time import sleep, time
import math
import json
import pigpio

from grafo_busca.grafo_busca import RobotLocationSystem, graph, directions
from robot_network.notification_listener import RobotNotificationListener

TESTING_NETWORK = False
from TCS3200 import *

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
        self.rpi.set_PWM_dutycycle(self.input[1], 255 * self.vel_l * 0.74 * self.vel_max)
        self.rpi.set_PWM_dutycycle(self.input[2], 0)
        self.rpi.set_PWM_dutycycle(self.input[3], 255 * self.vel_l * 0.74 * self.vel_max)
        self.rpi.set_PWM_dutycycle(self.input[4], 0)

    def turnRight(self):
        self.rpi.set_PWM_dutycycle(self.input[1], 0)
        self.rpi.set_PWM_dutycycle(self.input[2], 255 * self.vel_l * 0.74 * self.vel_max)
        self.rpi.set_PWM_dutycycle(self.input[3], 0)
        self.rpi.set_PWM_dutycycle(self.input[4], 255 * self.vel_r * 0.74 * self.vel_max)

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


class ColorSensor:
    """S0  S1        OUT frequency
    0   0   |          off
    0   1   |           2%
    1   0   |          20%
    1   1   |         100%
    --------------------------------
    S2  S3         Fotodiodo
    0   0   |          Red
    0   1   |         Blue
    1   0   |      w/ Filter
    1   1   |        Green
    --------------------------------
    OUT     Gives a value 0 - 255 of the color filter read
    """

    # sensor de cor vai ser usado só para ver se identificamos uma interseção ou uma vaga (vide foto_1.jpg)
    # vou utilizar as fotos da foto_1, vermelho pra rua e verde pra vaga
    def __init__(self, rpi, s0, s1, s2, s3, out):
        self.s = [s0, s1, s2, s3]  # do not use self.s[0]
        self.out = out
        self.rpi = rpi

        # for i in self.s:
        for i in self.s:  # desconsiderar o -1 na hr de setar os pinos
            self.rpi.set_mode(i, pigpio.OUTPUT)
        self.rpi.write(self.s[0], 1)
        self.rpi.write(self.s[1], 1)

        self.rpi.set_mode(out, pigpio.INPUT)

    def readRed(self):
        self.rpi.write(self.s[2], 0)
        self.rpi.write(self.s[3], 0)
        return self.rpi.get_PWM_dutycycle(self.out)

    def readGreen(self):
        self.rpi.write(self.s[2], 1)
        self.rpi.write(self.s[3], 1)
        return self.rpi.get_PWM_dutycycle(self.out)

    def readBlue(self):
        self.rpi.write(self.s[2], 0)
        self.rpi.write(self.s[3], 1)
        return self.rpi.get_PWM_dutycycle(self.out)

    def readAll(self):
        return self.readRed(), self.readGreen(), self.readBlue()

    def color(self):
        colors = list(self.readAll())  # returns red, green, blue into a list
        colors_backup = colors.copy()

        # Arredonda os valores para o numero mais próximo divisivel por 10
        # e acha o greate common divisor pra achar a ratio de vermelho, verde e azul
        colors = [20 * round(c / 20) for c in colors]
        div = math.gcd(math.gcd(colors[0], colors[1]), colors[2])
        print(colors, div)
        colors = [c / div for c in colors]

        red, green, blue = tuple(colors)
        if red > green and red > blue and green == blue:
            return "red"
        elif green > red and green > blue and red == blue:
            return "green"
        elif blue > red and blue > green and red == green:
            return "blue"
        elif red > blue and green > blue and red == green:
            return "yellow"
        elif blue > red and green > red and blue == green:
            return "cyan"
        elif red > green and blue > green and red == blue:
            return "magenta"
        elif red == green and green == blue and red == blue:
            if (
                colors_backup[0] > 125
                and colors_backup[1] > 125
                and colors_backup > 125
            ):
                return "white"
            else:
                return "black"


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

        StartTime = time()
        StopTime = time()

        # talvez se eu não apontar para uma parede não vai sair do while abaixo

        # save StartTime
        while not self.rpi.read(self.echo):
            StartTime = time()

        # save time of arrival
        while self.rpi.read(self.echo):
            StopTime = time()

        # time difference between start and arrival
        TimeElapsed = StopTime - StartTime
        # multiply with the sonic speed (34300 cm/s)
        # and divide by 2, because there and back
        distance = (TimeElapsed * 34300) / 2

        return distance


class Acelerometer:
    # https://www.youtube.com/watch?v=R0hjzhBlaHQ
    def __init__(self, rpi, acel_pins_list):
        self.rpi = rpi
        self.pins = acel_pins_list


class coneBot:
    def __init__(self):
        # Acho que vou criar uma classe para cada componente
        # Assim fica mais fácil setar, contorlar e ler coisas dos componentes

        self.led = 12

        self.buz = 12

        self.acel = [20, 21]

        self.rpi = pigpio.pi()

        self.motor = Motor(self.rpi, 2, 3, 4, 17)  # RPi pins for [IN1, IN2, IN3, IN4] motor driver
        self.tcrt = Tcrt5000(self.rpi, 5, 6, 13, 19, 26)  # RPi pins for [S1, S2, S3, S4, S5] tcrt5000 module
        self.color = ColorSensor(self.rpi, 27, 22, 10, 9, 11)  # RPi pins for [S0, S1, S2, S3] and OUT
        self.ultra = Ultrasonic(self.rpi, 23, 24)  # RPi pins for trig and echo

        # acelerometer fazer dpois, focar primeiro no motor e IR
        # self.acelerometer = Acelerometer(self.rpi, self.acel)

        self.location_system = RobotLocationSystem(graph, directions)
        if TESTING_NETWORK:
            self.notification_listener = RobotNotificationListener()
            self.notification_listener.listen()

        self.motor.stop()
        # self.start()

    def start(self):
        sleep(0.3)
        tcrt_values = self.tcrt.read()
        self.motor.moveProportional(tcrt_values)

        # fazer um while ultrasonico detectou fica parado
        # ler o sensor de cor e saber onde eu estou, guardar o status (localização)

    def test_motor(self):
        sleep(5)
        self.motor.setVel(0.4)
        while 1:
            print("go")
            self.motor.turnLeft()
            sleep(3)
            print("stop")
            self.motor.stop()
            sleep(3)
            print("goBack")
            self.motor.turnRight()
            sleep(3)
            print("stop")
            self.motor.stop()
            sleep(10)

    def test_tcrt(self):
        while 1:
            print(self.tcrt.read())

    def test_color(self):

        input("Calibrating black object, press RETURN to start")
        hz = self.color.get_hertz()
        # hz = [268.256, 247.957, 302.885]
        print(hz)
        self.color.set_black_level(hz)

        input("Calibrating white object, press RETURN to start")
        hz = self.color.get_hertz()
        # hz = [652.742, 633.967, 789.036]
        print(hz)
        self.color.set_white_level(hz)

        while 1:
            print(self.color.get_rgb(), self.color.color())
            sleep(0.5)

        self.color.cancel()
        self.pi.stop()

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
        state = 'straight'

        while 1:
            tcrt_read = self.tcrt.read()

            # estou assumindo que a posição 0 do tcrt_read seja a mais a esquerda do modulo, e a posição 4 a mais a direita

            # da forma como estava sendo feita, como você mesmo falou, nós só pegavamos essas combinações:
            # [1, 1, 0, 1, 1], [1, 0, 1, 1, 1], [1, 1, 1, 0, 1], [0, 1, 1, 1, 1], [1, 1, 1, 1, 0]
            # com esse código nós resolvemos os casos onde for detectado mais de um sensor

            if tcrt_read[0] == 0: # se o mais a esquerda detectou linha
                state = 'turning_left'
            
            elif tcrt_read[1] == 0: # ELIF, pq se eu ja peguei o sensor da extremidade posso ignorar esse pq tenho que virar bastante
                state = 'soft_turning_left'
            
            elif tcrt_read[4] == 0: # se o mais a direita detectou linha
                state = 'turning_right'

            elif tcrt_read[3] == 0: # se o sensor entre o central e o extremo da direita (extrema direita bolsonaro kkk)
                state = 'soft_turning_right'

            elif tcrt_read[2] == 0: # se pegou APENAS o sensor central pode pisar fundo 
                state = 'straight'
            
            if state == 'straight':
                print("1, 1")
                self.motor.setVelLeft(1)
                self.motor.setVelRight(1)
            elif state == 'soft_turning_right':
                print("0.8, 1")
                self.motor.setVelLeft(0.8)
                self.motor.setVelRight(1)
            elif state == 'turning_right':
                print("0.9, 0.4")
                self.motor.setVelLeft(0.9) # como a curva ta bem fechada acho interessante diminuir um pouco, pelo menos no primeiro teste
                self.motor.setVelRight(0.4)
            elif state == 'soft_turning_left':
                print("1, 0.8")
                self.motor.setVelLeft(1)
                self.motor.setVelRight(0.8)
            elif state == 'turning_left':
                print("0.4, 0.9")
                self.motor.setVelLeft(0.4)
                self.motor.setVelRight(0.9) # como a curva ta bem fechada acho interessante diminuir um pouco, pelo menos no primeiro teste
            
            self.motor.go()

        # podemos dar um break/stop se não identificar nada, podemos testar isso

    def followLineDumb(self):
        sleep(13)
        while 1:
            tcrt_read = self.tcrt.read()

            if tcrt_read == [1,1,0,1,1]:
                self.motor.setVelLeft(1)
                self.motor.setVelRight(1)
                self.motor.go()



            elif tcrt_read == [1,0,0,1,1]:
                self.motor.setVelLeft(1)
                self.motor.setVelRight(0.8)
                self.motor.go()
            
            elif tcrt_read == [1,0,1,1,1]:
                self.motor.setVelLeft(1)
                self.motor.setVelRight(0.6)
                self.motor.go()

            elif tcrt_read == [0,0,1,1,1]:
                self.motor.setVelLeft(1)
                self.motor.setVelRight(0.4)
                self.motor.go()

            elif tcrt_read == [0,1,1,1,1]:
                self.motor.turnLeft()



            elif tcrt_read == [1,1,0,0,1]:
                self.motor.setVelLeft(0.8)
                self.motor.setVelRight(1)
                self.motor.go()

            elif tcrt_read == [1,1,1,0,1]:
                self.motor.setVelLeft(0.6)
                self.motor.setVelRight(1)
                self.motor.go()

            elif tcrt_read == [1,1,1,0,0]:
                self.motor.setVelLeft(0.4)
                self.motor.setVelRight(1)
                self.motor.go()

            elif tcrt_read == [1,1,1,1,0]:
                self.motor.turnRight()

c = coneBot()

# c.start()
# c.test_motor()
# c.test_tcrt()
# c.test_color()
c.followLineDumb()
# c.start()
