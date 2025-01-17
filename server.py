from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib import parse
import numpy as np
import tensorflow as tf
import keras
import cv2
import os
import sys
from random import shuffle
from mtcnn.mtcnn import MTCNN
from keras.models import load_model
from PIL import Image
from scipy.special import softmax
import requests
from io import BytesIO
import io
import json

image_data = None

class requestHandler(BaseHTTPRequestHandler):

        
    def _set_headers(self, type):
        self.send_response(200)
        self.send_header('Content-Type', type)
        self.end_headers()
    
    def do_GET(self):
        print("GET")
        #self._set_headers()
        print(self.path)
        
        if self.path.startswith("/recognize") or self.path.startswith("/recognise"):    
            query_components = dict(parse.parse_qsl(parse.urlsplit(self.path).query))
            print(query_components)
            
            if "url" in query_components:
                url = query_components["url"]
                
                if url.startswith("http"):
                    faces = extract_faces_from_url(url)
                else:
                    faces = extract_faces_from_file(url)
                JSON = []
                
                for face, coordinates in faces:
                    distances = np.linalg.norm(get_embedding(face) - targets, axis = 1)
                    confidences = np.around(100 * softmax(-distances), decimals = 1)
                    label = people_list[np.argmax(confidences)]
                    max_confidence = np.max(confidences)
                    
                    x1, y1, x2, y2 = coordinates
                    
                    obj = {"name": label, "confidence": max_confidence, "box": {"x1": x1, "y1": y1, "x2": x2, "y2": y2}}
                    
                    JSON.append(obj)
                
                self._set_headers("application/json")
                self.wfile.write(json.dumps(JSON).encode())
                
            else:
                self._set_headers("text/html")
                self.wfile.write("'url' param not found <br>".encode())

        elif self.path.startswith("/image"):
            self._set_headers("image/png")
            self.wfile.write(image_data)
        else:
            file = open("index.html", "r")
            html = file.read()
            self._set_headers("text/html")
            self.wfile.write(html.encode())

            
        


def extract_faces_from_file(filename, required_size=(160, 160), verbose = False):
    
    image = Image.open(filename)
    
    global image_data
    imgByteArr = io.BytesIO()
    image.save(imgByteArr, format='PNG')
    image_data = imgByteArr.getvalue()
    
    image = image.convert('RGB')
    pixels = np.asarray(image)
    
    if verbose:
        plt.imshow(pixels)
        plt.show()
    
    detector = MTCNN()
    results = detector.detect_faces(pixels)
    
    if verbose:
        print(len(results), "faces detected")
    
    faces = []
    
    for face in results:
        x1, y1, width, height = face['box']
        x1, y1 = abs(x1), abs(y1)
        x2, y2 = x1 + width, y1 + height
        
        image = Image.fromarray(pixels[y1:y2, x1:x2])
        image = image.resize(required_size)
        faces.append((np.asarray(image), (x1, y1, x2, y2)))
    
    return faces

def extract_faces_from_url(url, required_size=(160, 160), verbose = False):
    
    response = requests.get(url)
    image = Image.open(BytesIO(response.content))
    
    global image_data
    imgByteArr = io.BytesIO()
    image.save(imgByteArr, format='PNG')
    image_data = imgByteArr.getvalue()
    
    image = image.convert('RGB')
    pixels = np.asarray(image)
    
    if verbose:
        plt.imshow(pixels)
        plt.show()
    
    detector = MTCNN()
    results = detector.detect_faces(pixels)
    
    if verbose:
        print(len(results), "faces detected")
    
    faces = []
    
    for face in results:
        x1, y1, width, height = face['box']
        x1, y1 = abs(x1), abs(y1)
        x2, y2 = x1 + width, y1 + height
        
        image = Image.fromarray(pixels[y1:y2, x1:x2])
        image = image.resize(required_size)
        faces.append((np.asarray(image), (x1, y1, x2, y2)))
    
    return faces

    
def get_embedding(face):
    face = face.astype('float32')
    mean, std = face.mean(), face.std()
    face = (face-mean)/std
    sample = np.expand_dims(face, axis=0)
    yhat = facenet_model.predict(sample)
    return yhat

def run():
    print("Starting server...")
    httpd = HTTPServer(('', 8080), requestHandler)
    print('Server running at localhost:8080...')
    httpd.serve_forever()

target_list = os.listdir('./res/vectors/')

if len(target_list) == 0:
    print("Vectors are missing. Please run generateVectors.py")
    sys.exit(-1)

print("Loading model...")
facenet_model = load_model('./model/facenet_keras.h5')

print("Loading targets...")
    
target_list = os.listdir('./res/vectors/')
targets = np.zeros((len(target_list), 128))

for index in range(len(target_list)):
    print('./res/vectors/' + target_list[index])
    vector = np.load('./res/vectors/' + target_list[index])        
    targets[index, :] = vector

people_list = [t.split(".")[0] for t in target_list]

print("")

run()
