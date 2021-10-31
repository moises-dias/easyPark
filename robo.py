# coding=utf-8

from time import sleep
import math
import json
import pigpio

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

        # preciso setar o modo dos pwm como output???

    def go(self):
        self.rpi.set_PWM_dutycycle(self.input[1], 255 * self.vel)
        self.rpi.set_PWM_dutycycle(self.input[2], 0)
        self.rpi.set_PWM_dutycycle(self.input[3], 255 * self.vel)
        self.rpi.set_PWM_dutycycle(self.input[4], 0)

    def turnLeft(self):
        self.rpi.set_PWM_dutycycle(self.input[1], 255 * self.vel)
        self.rpi.set_PWM_dutycycle(self.input[2], 0)
        self.rpi.set_PWM_dutycycle(self.input[3], 0)
        self.rpi.set_PWM_dutycycle(self.input[4], 255 * self.vel)

    def turnRight(self):
        self.rpi.set_PWM_dutycycle(self.input[1], 0)
        self.rpi.set_PWM_dutycycle(self.input[2], 255 * self.vel)
        self.rpi.set_PWM_dutycycle(self.input[3], 255 * self.vel)
        self.rpi.set_PWM_dutycycle(self.input[4], 0)

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
        self.rpi.set_PWM_dutycycle(self.input[1], 0)
        self.rpi.set_PWM_dutycycle(self.input[2], 255 * self.vel)
        self.rpi.set_PWM_dutycycle(self.input[3], 0)
        self.rpi.set_PWM_dutycycle(self.input[4], 255 * self.vel)

    def setVel(self, vel):
        if vel > 1 or vel < 0:
            raise "Seting motor velocity outside 0.0 - 1.0 range!"
        self.vel = vel

class ColorSensor:
    """ S0  S1        OUT frequency
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
    def __init__(self, rpi, s1, s2, s3, s4, out):
        self.s = [-1, s1, s2, s3, s4]   # do not use self.s[0]
        self.out = out
        self.rpi

        for i in self.s:
            self.rpi.set_mode(i, pigpio.OUTPUT)

        self.rpi.set_mode(i, pigpio.INPUT)

    def readRed(self):
        self.rpi.write(self.s[2], 0)
        self.rpi.write(self.s[3], 0)
        return self.read(self.out)

    def readGreen(self):
        self.rpi.write(self.s[2], 1)
        self.rpi.write(self.s[3], 1)
        return self.read(self.out)

    def readBlue(self):
        self.rpi.write(self.s[2], 0)
        self.rpi.write(self.s[3], 1)
        return self.read(self.out)

    def readAll(self):
        return self.readRed, self.readGreen, self.readBlue

    def readWithoutFilter(self):
        self.rpi.write(self.s[2], 1)
        self.rpi.write(self.s[3], 0)
        return self.read(self.out)

    def color(self):
        colors = [self.readAll()] # returns red, green, blue into a list
        colors_backup = colors.copy()
        
        # Arredonda os valores para o numero mais próximo divisivel por 10
        # e acha o greate common divisor pra achar a ratio de vermelho, verde e azul
        for c in colors:
            c = 10 * round(c / 10)
        div = math.gcd(colors[0], colors[1], colors[2])
        for c in colors:
            c = c / div
        
        red, green, blue = tuple(colors)
        if   red > green and red > blue and green == blue:
            return 'red'
        elif green > red and green > blue and red == blue:
            return 'green'
        elif blue > red and blue > green and red == green:
            return 'blue'
        elif red > blue and green > blue and red == green:
            return 'yellow'
        elif blue > red and green > red and blue == green:
            return 'cyan'
        elif red > green and blue > green and red == blue:
            return 'magenta'
        elif red == green and green == blue and red == blue:
            if colors_backup[0] > 125 and colors_backup[1] > 125 and colors_backup > 125:
                return 'white'
            else:
                return 'black'        

class tcrt5000:
    def __init__(self):
        pass

class Ultrassom:
    def __init__(self):
        pass


class coneBot:
    def __init__(self):
        # Acho que vou criar uma classe para cada componente
        # Assim fica mais fácil setar, contorlar e ler coisas dos componentes

        self.motor = Motor(2, 3, 4, 17)  # RPi pins for [IN1, IN2, IN3, IN4] motor driver
        
        self.cor_set = [27, 22, 10, 9] # RPi pins for [S1, S2, S3, S4]
        self.cor_out = 11 # RPi pins for OUT

        self.ir = [5, 6, 13, 19, 26] # RPi pins for [S1, S2, S3, S4, S5] tcrt5000 module

        self.ultrassom_trig = 23
        self.ultrassim_echo = 24

        self.led = 12

        self.buz = 12

        self.gyro = [20, 21]
        
        self.rpi = pigpio.pi()
        

        self.start()


    def start(self):

        pass


c = coneBot()
c.start()