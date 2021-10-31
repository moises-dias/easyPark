import pigpio
from motor import Motor
from colorSensor import ColorSensor
from tcrt import tcrt5000
from ultrassom import Ultrassom

class ConeBot:
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
