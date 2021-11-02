# coding=utf-8

from time import sleep, time
import math
import json
import pigpio

from TCS3200 import *

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
        self.vel_r = 1    # it ranges from 0 to 1
        self.vel_l = 1
        self.vel_max = 0.4
        self.stop() # garantir, vai q pino começa em high sei la

    def go(self):
        self.rpi.set_PWM_dutycycle(self.input[1], 0)
        self.rpi.set_PWM_dutycycle(self.input[2], 255 * self.vel_l * self.vel_max)
        self.rpi.set_PWM_dutycycle(self.input[3], 255 * self.vel_r * self.vel_max)
        self.rpi.set_PWM_dutycycle(self.input[4], 0)

    def turnLeft(self):
        self.rpi.set_PWM_dutycycle(self.input[1], 255 * self.vel * 0.74 * self.vel_max)
        self.rpi.set_PWM_dutycycle(self.input[2], 0)
        self.rpi.set_PWM_dutycycle(self.input[3], 255 * self.vel * 0.74 * self.vel_max)
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

    def setMaxVel(self, vel):
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
        self.color = ColorSensor(self.rpi, 11, 10, 9, 27, 22) # RPi pins for OUT, S2, S3, S0, S1
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

        input("Calibrating black object, press RETURN to start")
        hz = self.color.get_hertz()
        #hz = [268.256, 247.957, 302.885]
        print(hz)
        self.color.set_black_level(hz)

        input("Calibrating white object, press RETURN to start")
        hz = self.color.get_hertz()
        #hz = [652.742, 633.967, 789.036]
        print(hz)
        self.color.set_white_level(hz)

        while(1):
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
        while(1):
            tcrt_read = self.tcrt.read()
            print(tcrt_read)

            if tcrt_read == [1, 1, 0, 1, 1]:
                print('1, 1')
                self.motor.setVelLeft(1)
                self.motor.setVelRight(1)

            if tcrt_read == [1, 0, 1, 1, 1]:
                print('0.7, 1')
                self.motor.setVelLeft(0.7)
                self.motor.setVelRight(1)

            if tcrt_read == [1, 1, 1, 0, 1]:
                print('1, 0.7')
                self.motor.setVelLeft(1)
                self.motor.setVelRight(0.7)

            if tcrt_read == [0, 1, 1, 1, 1]:
                print('0.5, 1')
                self.motor.setVelLeft(0.5)
                self.motor.setVelRight(1)

            if tcrt_read == [1, 1, 1, 1, 0]:
                print('1, 0.5')
                self.motor.setVelLeft(1)
                self.motor.setVelRight(0.5)
            
            self.motor.go()

        # podemos dar um break/stop se não identificar nada, podemos testar isso

c = coneBot()
#c.test_motor()
#c.test_tcrt()
#c.test_color()
c.followLine()
#c.start()