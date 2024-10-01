import os
import cv2
import numpy as np
import argparse
import warnings
import time
import face_recognition_models
import face_recognition
import pickle
from PIL import Image, ImageDraw, ImageFont

from src.anti_spoof_predict import AntiSpoofPredict
from src.generate_patches import CropImage
from src.utility import parse_model_name
warnings.filterwarnings('ignore')

def liveness_check(frame, model_dir, device_id):
    model_test = AntiSpoofPredict(device_id)
    image_cropper = CropImage()
    test_result = []
    
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_loccations = face_recognition.face_locations(rgb_frame)
    
    if len(face_loccations) == 0:
        return []
        
    for face_location in face_loccations:
        top, right, bottom, left = face_location
        image_bbox = [left, top, right - left, bottom - top]
        prediction = np.zeros((1, 3))
        
        for model_name in os.listdir(model_dir):
            h_input, w_input, model_type, scale = parse_model_name(model_name)
            param = {
                "org_img": frame,
                "bbox": image_bbox,
                "scale": scale,
                "out_w": w_input,
                "out_h": h_input,
                "crop": True,
            }
            
            if scale is None:
                param["crop"] = False
            img = image_cropper.crop(**param)
            prediction += model_test.predict(img, os.path.join(model_dir, model_name))
            
        label = np.argmax(prediction)
        value = prediction[0][label] / 2
        
        lab_val = (label, value, face_location)
        test_result.append(lab_val)
        
    return test_result

def predict(X_frame, knn_clf=None, model_path=None, distance_threshold=0.4):
    """
    Recognizes faces in given image using a trained KNN classifier

    :param X_frame: frame to do the prediction on.
    :param knn_clf: (optional) a knn classifier object. if not specified, model_save_path must be specified.
    :param model_path: (optional) path to a pickled knn classifier. if not specified, model_save_path must be knn_clf.
    :param distance_threshold: (optional) distance threshold for face classification. the larger it is, the more chance
           of mis-classifying an unknown person as a known one.
    :return: a list of names and face locations for the recognized faces in the image: [(name, bounding box), ...].
        For faces of unrecognized persons, the name 'unknown' will be returned.
    """
    if knn_clf is None and model_path is None:
        raise Exception("File Encoding Tidak Ditemukan")
    
    if knn_clf is None:
        with open(model_path, 'rb') as f:
            knn_clf = pickle.load(f)
    
    predictions = []
    
    desc = "liveness_check"
    parser = argparse.ArgumentParser(description = desc)
    parser.add_argument(
        "--model_dir",
        type=str,
        default="./resources/anti_spoof_models",
        help="model_lib used to test"
    )
    args = parser.parse_args()
    
    liveness = liveness_check(X_frame, args.model_dir, 0)
    if len(liveness) == 0:
        return []
    
    if len(liveness) > 1:
        return [("Lebih dari Satu Wajah", liveness[0][2], 10, 10)]
    
    X_label = []
    X_value = []
    X_face_locations = []
    for data in liveness:
        X_label.append(data[0])
        X_value.append(data[1])
        X_face_locations.append(data[2])
        
    face_encodings = face_recognition.face_encodings(X_frame, known_face_locations = X_face_locations)
    closest_distances = knn_clf.kneighbors(face_encodings, n_neighbors = 1)
    are_matches = [closest_distances[0][i][0] <= distance_threshold for i in range(len(face_encodings))]

    for pred, loc, rec, label, value in zip(knn_clf.predict(face_encodings), X_face_locations, are_matches, X_label, X_value):
        if rec and label == 1:
            predictions.append((pred, loc, label, value))
        elif rec and label != 1:
            pred_ = "{}, Palsu".format(pred)
            predictions.append((pred_, loc, label, value))
        elif label != 1:
            predictions.append(("Palsu", loc, label, value))
        else:
            predictions.append(("Tidak Dikenali", loc, label, value))
            
    # print(pred)
    return predictions