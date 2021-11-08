import RPi.GPIO as GPIO
import time

leds = {'R': 5, 'G': 7, 'B': 11}
entering_button = 22
leaving_button = 31

parked = ['a', 'b', 'c']
entering_list = ['c', 'd', 'e']
leaving_list = ['d', 'e', 'f']
entering_index = 0
leaving_index = 0


GPIO.setmode(GPIO.BOARD)
GPIO.setup(leds['R'], GPIO.OUT)
GPIO.setup(leds['G'], GPIO.OUT)
GPIO.setup(leds['B'], GPIO.OUT)
GPIO.setup(entering_button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(leaving_button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.output(leds['R'], True)
GPIO.output(leds['G'], True)
GPIO.output(leds['B'], True)

print('starting')
GPIO.output(leds['R'], False)
while (GPIO.input(entering_button) or GPIO.input(leaving_button)):
    time.sleep(1)
    if not GPIO.input(entering_button):
        GPIO.output(leds['R'], True)
        GPIO.output(leds['B'], False)
        print('lendo placa para entrada')
        if True: # se placa lida
            if not entering_list[entering_index] in parked:
                print(f"{entering_list[entering_index]} estacionou")
                parked.append(entering_list[entering_index])
                GPIO.output(leds['B'], True)
                GPIO.output(leds['G'], False)
                print('cancela abrindo por 5 segundos')
                time.sleep(5)
                GPIO.output(leds['G'], True)
                GPIO.output(leds['R'], False)
                print('cancela fechando')
            else:
                print('erro, carro já estacionado')
                GPIO.output(leds['B'], True)
                GPIO.output(leds['R'], False)
        entering_index = entering_index + 1
    elif not GPIO.input(leaving_button):
        GPIO.output(leds['R'], True)
        GPIO.output(leds['B'], False)
        print('lendo placa para saida')
        if True: # se placa lida
            if leaving_list[leaving_index] in parked:
                print(f"{leaving_list[leaving_index]} saiu")
                parked.remove(leaving_list[leaving_index])
                GPIO.output(leds['B'], True)
                GPIO.output(leds['G'], False)
                print('cancela abrindo por 5 segundos')
                time.sleep(5)
                GPIO.output(leds['G'], True)
                GPIO.output(leds['R'], False)
                print('cancela fechando')
            else:
                print('erro, carro nao entrou')
                GPIO.output(leds['B'], True)
                GPIO.output(leds['R'], False)
        leaving_index = leaving_index + 1





# for x in range(10):
#     GPIO.output(7, True)
#     time.sleep(1)
#     GPIO.output(7, False)
#     time.sleep(1)
#     if not GPIO.input(11):
#         print('apertou botão')
#     print(x)
# for x in range(10):
#     GPIO.output(7, not GPIO.input(11))
#     time.sleep(1)
