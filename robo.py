# coding=utf-8

from time import sleep, time
from datetime import datetime
import math
import json
import numpy as np
import pigpio
from threading import Thread

import requests


from grafo_busca.grafo_busca import RobotLocationSystem, graph, directions, vagas
from robot_network.notification_listener import RobotNotificationListener
from queue import Queue

# from rasp_camera_detection_v4 import setup, get_plate_string

try:
    from TCS3200 import *
    from MPU6050 import *
except ModuleNotFoundError:
    print("Módulos do RPi não encontrados. Prosseguindo.")

TESTING_PLATE_RECOGNITION = False
PLATE_SERVER_URL = "https://easy-park-iw.herokuapp.com/user/linkUserToSpot"
BEGIN_SESSION_URL = "https://easy-park-iw.herokuapp.com/user/beginSession"

# pigpio documentation
# http://abyz.me.uk/rpi/pigpio/python.html

# CARREGANDO AS TRANQUEIRA DE IMAGEM
if TESTING_PLATE_RECOGNITION:
    # remove warning message
    import os
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

    # required library
    import cv2
    import numpy as np
    from local_utils import detect_lp
    from os.path import splitext
    from keras.models import model_from_json
    from sklearn.preprocessing import LabelEncoder
    import time
    from picamera import PiCamera
    from os import listdir, rename

    #test
    import tensorflow as tf
    from tensorflow import keras
    session = tf.Session()
    keras.backend.set_session(session)


    camera = PiCamera()
    # camera.rotation = 180
    camera.resolution = (640, 480)

    def load_model(path):
        try:
            path = splitext(path)[0]
            with open('%s.json' % path, 'r') as json_file:
                model_json = json_file.read()
            model = model_from_json(model_json, custom_objects={})
            model.load_weights('%s.h5' % path)
            model._make_predict_function()
            return model
        except Exception as e:
            print(e)

    def preprocess_image(image_path,resize=False):
        img = cv2.imread(image_path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = img / 255
        if resize:
            img = cv2.resize(img, (224,224))
        return img

    def get_plate(image_path, Dmax=608, Dmin = 608):
        vehicle = preprocess_image(image_path, True) # ----------------------------- ver se é melhor com ou sem resize
        ratio = float(max(vehicle.shape[:2])) / min(vehicle.shape[:2])
        side = int(ratio * Dmin)
        bound_dim = min(side, Dmax)
        _ , LpImg, _, cor = detect_lp(wpod_net, vehicle, bound_dim, lp_threshold=0.5)
        return vehicle, LpImg, cor

    # Create sort_contours() function to grab the contour of each digit from left to right
    def sort_contours(cnts,reverse = False):
        i = 0
        boundingBoxes = [cv2.boundingRect(c) for c in cnts]
        (cnts, boundingBoxes) = zip(*sorted(zip(cnts, boundingBoxes), key=lambda b: b[1][i], reverse=reverse))
        return cnts

    # pre-processing input images and pedict with model
    def predict_from_model(image,model,labels):
        image = cv2.resize(image,(80,80))
        image = np.stack((image,)*3, axis=-1)
        prediction = labels.inverse_transform([np.argmax(model.predict(image[np.newaxis,:]))])
        return prediction

    def filter_digits(cont, plate_image, thre_mor):
        crop_characters = []
        # define standard width and height of character
        digit_w, digit_h = 30, 60
        for c in sort_contours(cont):
            (x, y, w, h) = cv2.boundingRect(c)
            if 0.35 < (w/h) < 1.2: # se a divisão da largura pela altura está no intervalo (0.35, 1.2)
                if 0.03 < ((w*h)/(plate_image.shape[0] * plate_image.shape[1])) < 0.1: # se a área do identificado/area da imagem está entre (0.03, 0.1)
                    # Sperate number and gibe prediction
                    curr_num = thre_mor[y:y+h,x:x+w]
                    curr_num = cv2.resize(curr_num, dsize=(digit_w, digit_h))
                    _, curr_num = cv2.threshold(curr_num, 220, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                    crop_characters.append(curr_num)
        return crop_characters

    wpod_net_path = "wpod-net.json"
    wpod_net = load_model(wpod_net_path)

    # Load model architecture, weight and labels
    json_file = open('MobileNets_character_recognition.json', 'r')
    loaded_model_json = json_file.read()
    json_file.close()
    model = model_from_json(loaded_model_json)
    model.load_weights("License_character_recognition_weight.h5")
    model._make_predict_function()

    labels = LabelEncoder()
    labels.classes_ = np.load('license_character_classes.npy')

    print('model was loaded!')
    time.sleep(1)

def reset_model():
    session = tf.Session()
    keras.backend.set_session(session)


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
        self.sound = 800

        self.rpi = pigpio.pi()

        # RPi pins for [IN1, IN2, IN3, IN4] motor driver
        self.motor = Motor(self.rpi, 13, 16, 20, 21)

        # RPi pins for [S1, S2, S3, S4, S5] tcrt5000 module
        self.tcrt = Tcrt50005Channel(self.rpi, 4, 18, 17, 27, 23)

        # RPi pins for
        self.tcrt_side = Tcrt50001Channel(self.rpi, 11)

        # RPi pins for OUT, S2, S3, S0, S1
        # self.color = ColorSensor(self.rpi, 6, 12, 5, 11, 7)

        self.ultra = Ultrasonic(self.rpi, 24, 10)  # RPi pins for trig and echo
        self.gyro = Gyroscope(self.rpi)

        self.location_system = RobotLocationSystem(graph, directions)
        self.node_pos = 0
        self.face = "U"
        self.spot = vagas[self.node_pos][self.face]
        self.establishment = "61a3bd0da338eb4b5442dbaa"
        #requests.post(BEGIN_SESSION_URL, json={"establishment": self.establishment, "plate": "BEE4R22"})

        self.motor.stop()
        # except Exception:
        #    print(f"You're not using a RPi. Continuing.")

        # if TESTING_PLATE_RECOGNITION:
        #     self.model, self.labels = setup()

        self.start_bot()

    def run(self):
        dispatcher_thread.register_interest(self)

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

            # next_node, next_face = self.get_next_serviced_spot()
            # print(f"Going to {next_node}, {next_face}")
            # self.move_on_parking_lot_from_message(next_node, next_face)

            self.moveOnParkingLot()
            break  # This is here just for testing purposes

    def put_message(self, message):
        self.pspot_queue.put(message)

    def start_bot(self):

        self.motor.setVelMax(0.34)

    def soundAlarm(self):
        if self.sound == 800:
            self.sound = 1500
        else:
            self.sound = 800

        self.rpi.set_PWM_dutycycle(self.buz, 128)  #  50 %
        self.rpi.set_PWM_frequency(self.buz, self.sound)

    def followLine(self):
        tcrt_read = self.tcrt.read()

        g = np.round(list(self.gyro.read_acc()), 4)
        print(abs(g[0]), abs(g[1]), self.ultra.measure_distance())
        while self.ultra.measure_distance() < 10.0 or abs(g[0]) > 0.35 or abs(g[1] > 0.35):  # Se entrar algo na frente, espera (pooling)
            self.soundAlarm();
            self.motor.brake()
            sleep(0.16)

        if tcrt_read == [1, 1, 0, 1, 1]:
            self.motor.setVelLeft(0.8)
            self.motor.setVelRight(0.79)
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

        else:
            self.motor.setVelLeft(0.8)
            self.motor.setVelRight(0.79)
            self.motor.go()

    def turn(self, direction):

        self.motor.setVelLeft(0.9)
        self.motor.setVelRight(0.9)

        # manda o robo fazer a curva
        if direction == "L":
            self.motor.turnLeftSpike()
            # self.motor.turnLeft()
        else:
            self.motor.turnRightSpike()
            # self.motor.turnRight()

        ti = time.time()
        tf = time.time()

        while (tf - ti) < 0.6:
            tf = time.time()

        while not self.tcrt_side.read():  # Enquanto black
            pass

        while self.tcrt_side.read():  # Enquanto white
            pass

        if direction == "L":
            self.motor.turnRight()
            sleep(0.09)
            # self.motor.turnLeft()
        else:
            self.motor.turnLeft()
            sleep(0.09)
            # self.motor.turnRight()

        self.motor.brake()

    def moveStraight(self):
        ti = time.time()
        tf = time.time()

        while (tf - ti) < 0.6:
            tf = time.time()
            self.followLine()

        while not self.tcrt_side.read():  # Enquanto black
            self.followLine()

        self.motor.setVelLeft(1)
        self.motor.setVelRight(1)

        while self.tcrt_side.read():  # Enquanto white
            self.followLine()

        self.motor.brake()

        self.motor.setVelLeft(1)  # preciso resetar, pq o followLine altera as velocidades dos motores
        self.motor.setVelRight(1)  # conforme necessidade, ai pode ter acabado o while com velocidades diferentes que 1

        self.motor.goBack()
        sleep(0.09)
        self.motor.brake()

    def moveOnParkingLot(self):
        self.motor.stop()
        # sleep(13)
        face = "R"
        spot = 6

        end = 1
        end_dir = "R"

        while True:
            face, operations = self.location_system.get_path(spot, face, end, end_dir)
            print(operations)  # se quiser ver o trajeto retornado

            print("--------- ROBOT ON ---------")
            for action in operations:
                sleep(2)
                if action in ["R", "L"]:
                    print("Turning " + action)
                    #self.turn(action)
                    sleep(3)
                elif action in ["180"]:
                    print("Turning " + "R")
                    self.turn(action)
                    sleep(3)
                    print("Turning " + "R")
                    self.turn(action)
                    sleep(3)
                else:
                    print("Move straight")
                    self.moveStraight()
                    sleep(3)

            print("--------- FINISH ---------")

            print("Getting foto! smile :)")
            sleep(4)

            spot = end
            face = end_dir

            end = 5
            end_dir = "D"

    def move_on_parking_lot_from_message(self, destination_node: int, destination_face: str):
        """Not-hardcoded version of moveOnParkingLot"""
        self.motor.stop()
        sleep(20)

        face, operations = self.location_system.get_path(self.node_pos, self.face, destination_node, destination_face)
        print(f"Operations needed to get to destination: {operations}")

        print("--------- ROBOT ON ---------")
        for action in operations:
            sleep(0.5)
            if action in ["R", "L"]:
                print("Turning " + action)
                self.turn(action)
            elif action in ["180"]:
                print("Turning " + "R")
                self.turn(action)
                print("Turning " + "R")
                self.turn(action)
            else:
                print("Move straight")
                self.moveStraight()
        print("Getting foto! smile :)")
        self.node_pos = destination_node
        self.face = destination_face
        self.vaga = vagas[self.node_pos][self.face]
        if TESTING_PLATE_RECOGNITION:
            self.send_plate_info_to_server()

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
        if TESTING_PLATE_RECOGNITION:
            print("TIRANDO FOTO")
            camera.start_preview()
            print('detectando em 3 segundos')
            time.sleep(3)

            numfiles = len([f for f in listdir('./Plate_examples')])
            camera.capture(f'./Plate_examples/img{numfiles}.jpg')
            camera.stop_preview()
            test_image_path = f"Plate_examples/img{numfiles}.jpg"
            # reset_model()
            # session = tf.Session()
            # keras.backend.set_session(session)
            with session.as_default():
                with session.graph.as_default():
                    vehicle, LpImg ,cor = get_plate(test_image_path)

            if (len(LpImg)): #check if there is at least one license image
                # Scales, calculates absolute values, and converts the result to 8-bit.
                plate_image = cv2.convertScaleAbs(LpImg[0], alpha=(255.0))
                
                # convert to grayscale and blur the image
                gray = cv2.cvtColor(plate_image, cv2.COLOR_BGR2GRAY)
                blur = cv2.GaussianBlur(gray,(7,7),0) 
                binary = cv2.threshold(blur, 180, 255,cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
                kernel3 = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
                thre_mor = cv2.morphologyEx(binary, cv2.MORPH_DILATE, kernel3)
            else:
                print(f"img{numfiles}.jpg", 'no plate found')
                # raise ValueError('No Plate Found!')
                return

            cont, _  = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

            crop_characters = filter_digits(cont, plate_image, thre_mor)

            if len(crop_characters) != 7:
                print(f"img{numfiles}.jpg", 'not found 7 digits')
                print(crop_characters)
                # raise ValueError(f'Identified {len(crop_characters)} digits, the correct should be 7.')
                return

            final_string = ''
            for i,character in enumerate(crop_characters):
                with session.as_default():
                    with session.graph.as_default():
                        title = np.array2string(predict_from_model(character,model,labels))
                final_string+=title.strip("'[]")

            print(f"img{numfiles}.jpg", final_string)
            rename(f"Plate_examples/img{numfiles}.jpg", f"Plate_examples/img{numfiles}_{final_string}.jpg")
            
            plate_string = final_string
            requests.post(PLATE_SERVER_URL, json={"plate": plate_string, "spot": self.vaga})
        else:
            print("Não estamos testando reconhecimento de placas agora.")

    def get_next_serviced_spot(self):
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
