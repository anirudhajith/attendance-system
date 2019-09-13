import numpy as np
import tensorflow as tf
import keras
import cv2
import os
import sys
from mtcnn.mtcnn import MTCNN
from keras.models import load_model
from PIL import Image
from scipy.special import softmax
import requests
from io import BytesIO
import io
import json

def extract_faces_from_file(filename, required_size=(160, 160)):
    
    image = Image.open(filename).convert('RGB')
    pixels = np.asarray(image)
    
    detector = MTCNN()
    results = detector.detect_faces(pixels)
    
    faces = []
    
    for face_data_item in results:
        x1, y1, width, height = face_data_item['box']
        x1, y1 = abs(x1), abs(y1)
        x2, y2 = x1 + width, y1 + height
        face_image = Image.fromarray(pixels[y1:y2, x1:x2]).resize(required_size)
        
        faces.append((np.asarray(face_image), (x1, y1, x2, y2)))
    
    return faces

def extract_faces_from_url(url, required_size=(160, 160)):
    
    response = requests.get(url)
    image = Image.open(BytesIO(response.content)).convert('RGB')
    pixels = np.asarray(image)
    
    detector = MTCNN()
    results = detector.detect_faces(pixels)
    
    faces = []
    
    for face_data_item in results:
        x1, y1, width, height = face_data_item['box']
        x1, y1 = abs(x1), abs(y1)
        x2, y2 = x1 + width, y1 + height
        face_image = Image.fromarray(pixels[y1:y2, x1:x2]).resize(required_size)
        
        faces.append((np.asarray(face_image), (x1, y1, x2, y2)))
    
    return faces

def get_embedding(face_image_array):
    face_image_array = face_image_array.astype('float32')
    mean, std = face_image_array.mean(), face_image_array.std()
    face_image_array = (face_image_array - mean)/std
    sample = np.expand_dims(face_image_array, axis=0)
    embedding = facenet_model.predict(sample)
    return embedding

if os.path.isfile('./model/facenet_keras.h5'): 
    print("Loading model...")
    facenet_model = load_model('./model/facenet_keras.h5')
else:
    print("Model not found. Please download from github.com/anirudhajith/attendance-system.git")
    sys.exit(-1)