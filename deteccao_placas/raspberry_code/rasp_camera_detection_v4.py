#!/usr/bin/env python3
# coding: utf-8

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
import requests
import json


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

def filter_digits(cont):
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

labels = LabelEncoder()
labels.classes_ = np.load('license_character_classes.npy')

print('model was loaded!')
time.sleep(1)
while True:
    time.sleep(5)
    camera.start_preview()
    time.sleep(3)

    numfiles = len([f for f in listdir('./Plate_examples')])
    camera.capture(f'./Plate_examples/img{numfiles}.jpg')
    camera.stop_preview()
    test_image_path = f"Plate_examples/img{numfiles}.jpg"
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

    cont, _  = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    crop_characters = filter_digits(cont)

    if len(crop_characters) != 7:
        print(f"img{numfiles}.jpg", 'not found 7 digits')
        # raise ValueError(f'Identified {len(crop_characters)} digits, the correct should be 7.')

    final_string = ''
    for i,character in enumerate(crop_characters):
        title = np.array2string(predict_from_model(character,model,labels))
        final_string+=title.strip("'[]")

    print(f"img{numfiles}.jpg", final_string)
    rename(f"Plate_examples/img{numfiles}.jpg", f"Plate_examples/img{numfiles}_{final_string}.jpg")

    # print('making a POST request...')

    # url = f'https://easy-park-iw.herokuapp.com/user/{operation}'
    # myobj = {'establishment': '616e177497e39946b8d6c2fa', 'plate': final_string}
    # headers={'Content-type':'application/json'}

    # req = requests.post(url, json = myobj, headers=headers)

    # print(req.text)

    # if json.loads(req.text)['success']:
    #     print('request successful')
    # else:
    #     print(json.loads(req.text)['messages'])
