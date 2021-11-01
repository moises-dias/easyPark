# coding=utf-8

from time import sleep, time
import math
import json
import pigpio

from .TCS3200 import *

# pigpio documentation
# http://abyz.me.uk/rpi/pigpio/python.html

class Motor:
    """ IN1     IN2 | Motor right (top view with front facing up)
        IN3     IN4 | Motor left
        ------------------------------------
        255     0   | ahead
        0       255 | back
        0       0   | idle
        255     255 | brake
    """

    def __init__(self, rpi, IN1, IN2, IN3, IN4):
        self.input = [-1, IN1, IN2, IN3, IN4] # do not use self.input[0]
        self.rpi = rpi
        self.vel = 1    # it ranges from 0 to 1
        self.stop() # garantir, vai q pino começa em high sei la

        # preciso setar o modo dos pwm como output???
        # boa pergunta, mas podemos testar, vai ser facil de achar
    
    # podemos criar métodos para virar proporcionalmente dependendo do output do tcrt
    # pelo que eu entendi:
    # 1 = motor r frente
    # 2 = motor r trás
    # 3 = motor l frente
    # 4 = motor l trás
    def moveProportional(self, tcrt): 
        # tcrt é uma lista de bool com 5 itens, referentes a leitura do tcrt
        # indo da esquerda para a direita
        vel_l = 0
        vel_r = 0
        if tcrt[2]: # se o IR central está vendo linha 
            # seta a velocidade no maximo
            vel_r = 1
            vel_l = 1
        if tcrt[1]: # se o primeiro sensor a esquerda do central está vendo linha
            # diminui um pouco a velocidade do motor da esquerda, virar pra esquerda
            vel_r = 1
            vel_l = 0.8
        if tcrt[3]: # se o primeiro sensor a direita do central está vendo linha
            # diminui um pouco a velocidade do motor da direta, virar para direita
            vel_r = 0.8
            vel_l = 1
        if tcrt[0]: # se o segundo sensor a esquerda do central esta vendo linha
            # diminui mais ainda a velocidade do esquerdo
            vel_r = 1
            vel_l = 0.4
        if tcrt[4]: # se o segundo sensor a direita do central está vendo linha
            # diminui mais ainda a velocidade do motor direito
            vel_r = 0.4
            vel_l = 1
        
        # setando velocidades
        self.rpi.set_PWM_dutycycle(self.input[1], 255 * vel_r)
        self.rpi.set_PWM_dutycycle(self.input[2], 0)
        self.rpi.set_PWM_dutycycle(self.input[3], 255 * vel_l)
        self.rpi.set_PWM_dutycycle(self.input[4], 0)

        # podemos dar um break/stop se não identificar nada, podemos testar isso

    def go(self):
        self.rpi.set_PWM_dutycycle(self.input[1], 0)
        self.rpi.set_PWM_dutycycle(self.input[2], 255 * self.vel)
        self.rpi.set_PWM_dutycycle(self.input[3], 255 * self.vel)
        self.rpi.set_PWM_dutycycle(self.input[4], 0)

    def turnLeft(self):
        self.rpi.set_PWM_dutycycle(self.input[1], 255 * self.vel * 0.74)
        self.rpi.set_PWM_dutycycle(self.input[2], 0)
        self.rpi.set_PWM_dutycycle(self.input[3], 255 * self.vel * 0.74)
        self.rpi.set_PWM_dutycycle(self.input[4], 0)

    def turnRight(self):
        self.rpi.set_PWM_dutycycle(self.input[1], 0)
        self.rpi.set_PWM_dutycycle(self.input[2], 255 * self.vel * 0.74)
        self.rpi.set_PWM_dutycycle(self.input[3], 0)
        self.rpi.set_PWM_dutycycle(self.input[4], 255 * self.vel * 0.74)

    def stop(self):
        self.rpi.set_PWM_dutycycle(self.input[1], 0)
        self.rpi.set_PWM_dutycycle(self.input[2], 0)
        self.rpi.set_PWM_dutycycle(self.input[3], 0)
        self.rpi.set_PWM_dutycycle(self.input[4], 0)

    def brake(self):
        self.rpi.set_PWM_dutycycle(self.input[1], 255 * self.vel)
        self.rpi.set_PWM_dutycycle(self.input[2], 255 * self.vel)
        self.rpi.set_PWM_dutycycle(self.input[3], 255 * self.vel)
        self.rpi.set_PWM_dutycycle(self.input[4], 255 * self.vel)

    def goBack(self):
        self.rpi.set_PWM_dutycycle(self.input[1], 255 * self.vel)
        self.rpi.set_PWM_dutycycle(self.input[2], 0)
        self.rpi.set_PWM_dutycycle(self.input[3], 0)
        self.rpi.set_PWM_dutycycle(self.input[4], 255 * self.vel)

    def setVel(self, vel):
        if vel > 1:
            vel = 1
        elif vel < 0:
            vel = 0
        # acho q levantar um raise pode travar o robo no meio do estacionamento
        # if vel > 1 or vel < 0:
        #     raise "Seting motor velocity outside 0.0 - 1.0 range!"
        self.vel = vel

class Tcrt5000:
    # https://thepihut.com/blogs/raspberry-pi-tutorials/how-to-use-the-tcrt5000-ir-line-follower-sensor-with-the-raspberry-pi
    # código baseado no tutorial acima
    def __init__(self, rpi, s1, s2, s3, s4, s5):
        self.sensors = [-1, s1, s2, s3, s4, s5]
        self.rpi = rpi
        for i in self.sensors[1:]:
            self.rpi.set_mode(i, pigpio.INPUT)
    
    def read(self):
        sensor_values = []
        for s in self.sensors[1:]:
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
        self.tcrt = Tcrt5000(self.rpi, 5, 6, 13, 19, 26) # RPi pins for [S1, S2, S3, S4, S5] tcrt5000 module
        self.color = ColorSensor(self.rpi, 27, 22, 10, 9, 11) # RPi pins for [S0, S1, S2, S3] and OUT
        self.ultra = Ultrasonic(self.rpi, 23, 24) # RPi pins for trig and echo
        
        # acelerometer fazer dpois, focar primeiro no motor e IR
        #self.acelerometer = Acelerometer(self.rpi, self.acel)

        #self.start()


    def start(self):
        sleep(0.3)
        tcrt_values = self.tcrt.read()
        self.motor.moveProportional(tcrt_values)
        
        # fazer um while ultrasonico detectou fica parado
        # ler o sensor de cor e saber onde eu estou, guardar o status (localização)

    def test_motor(self):
        sleep(5)
        self.motor.setVel(0.4)
        while(1):
            print('go')
            self.motor.turnLeft()
            sleep(3)
            print('stop')
            self.motor.stop()
            sleep(3)
            print('goBack')
            self.motor.turnRight()
            sleep(3)
            print('stop')
            self.motor.stop()
            sleep(10)

    def test_tcrt(self):
        while(1):
            print(self.tcrt.read())

    def test_color(self):

        wait_for_return("Calibrating black object, press RETURN to start")
        hz = self.color.get_hertz()
        self.color.set_black_level(hz)

        wait_for_return("Calibrating white object, press RETURN to start")
        hz = self.color.get_hertz()
        self.color.set_white_level(hz)

        while(1):
            print(self.color.get_rgb(), self.color.color())
            sleep(0.5)

        self.color.cancel()
        self.pi.stop()


c = coneBot()
#c.test_motor()
#c.test_tcrt()
c.test_color()
#c.start()