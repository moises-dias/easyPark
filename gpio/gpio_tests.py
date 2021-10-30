import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BOARD)
GPIO.setup(7, GPIO.OUT)
GPIO.setup(11, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.output(7, True)
for x in range(10):
    GPIO.output(7, True)
    time.sleep(1)
    GPIO.output(7, False)
    time.sleep(1)
    if not GPIO.input(11):
        print('apertou botão')
    print(x)
for x in range(10):
    GPIO.output(7, not GPIO.input(11))
    time.sleep(1)
