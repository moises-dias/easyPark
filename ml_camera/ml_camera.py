import RPi.GPIO as GPIO
import time
import cv2
from picamera.array import PiRGBArray
from picamera import PiCamera

GPIO.setmode(GPIO.BOARD)
GPIO.setup(11, GPIO.IN, pull_up_down=GPIO.PUD_UP)

camera = PiCamera()

while True:
    time.sleep(1)
    if not GPIO.input(11):
        print('Apertou Botão')
        rawCapture = PiRGBArray(camera)
        # allow the camera to warmup
        time.sleep(2)
        # grab an image from the camera
        camera.capture(rawCapture, format="bgr")
        image = rawCapture.array
        # display the image on screen and wait for a keypress
        cv2.imshow("Image", image)
        cv2.waitKey(0)
