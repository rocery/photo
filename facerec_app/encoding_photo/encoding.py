import face_recognition_models
import face_recognition
from face_recognition.face_recognition_cli import image_files_in_folder
import math
from sklearn import neighbors
import os
import os.path
import pickle
import csv
import time
import shutil
from datetime import datetime

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'JPG'}

train_folder = "train"
fail_folder = "fail"
model_save_path = "../static/clf/trained_knn_model.clf"
csv_success = "success_trained.csv"
csv_fail = "fail_trained.csv"

def train(train_dir, model_save_path=None, n_neighbors=None, knn_algo='ball_tree', verbose=True):
    """
    Trains a k-nearest neighbors classifier for face recognition.

    :param train_dir: directory that contains a sub-directory for each known person, with its name.

    (View in source code to see train_dir example tree structure)

    Structure:
        <train_dir>/
        ├── <person1>/
        │   ├── <somename1>.jpeg
        │   ├── <somename2>.jpeg
        │   ├── ...
        ├── <person2>/
        │   ├── <somename1>.jpeg
        │   └── <somename2>.jpeg
        └── ...

    :param model_save_path: (optional) path to save model on disk
    :param n_neighbors: (optional) number of neighbors to weigh in classification. Chosen automatically if not specified
    :param knn_algo: (optional) underlying data structure to support knn.default is ball_tree
    :param verbose: verbosity of training
    :return: returns knn classifier that was trained on the given data.
    """
    X = []
    y = []
    
    folder_counter = 0
    img_counter = 0
    failed_images_counter = 0
    total_time_encoding = 0

    # Loop through each person in the training set
    for class_dir in os.listdir(train_dir):
        if not os.path.isdir(os.path.join(train_dir, class_dir)):
            continue

        folder_counter += 1
        # Loop through each training image for the current person
        for img_path in image_files_in_folder(os.path.join(train_dir, class_dir)):
            start_time_encoding = time.time()
            image = face_recognition.load_image_file(img_path)
            face_bounding_boxes = face_recognition.face_locations(image)
            img_counter += 1
            
            if len(face_bounding_boxes) != 1:
                # If there are no people (or too many people) in a training image, skip the image.
                if verbose:
                    print("Image {} not suitable for training: {}".format(img_path, "Didn't find a face" if len(face_bounding_boxes) < 1 else "Found more than one face"))
                    failed_images_counter += 1
                    
                    
                    with open (csv_fail, mode='a', newline='') as file:
                        writer = csv.writer(file)
                        now = datetime.now()
                        writer.writerow([img_counter, class_dir, img_path, "Wajah tidak terdeteksi" if len(face_bounding_boxes) < 1 else "Wajah terdeteksi lebih dari 1", now.strftime("%Y-%m-%d %H:%M:%S")])
                shutil.move(img_path, os.path.join(fail_folder, os.path.basename(img_path)))         
                
            else:
                # Add face encoding for current image to the training set
                X.append(face_recognition.face_encodings(image, known_face_locations=face_bounding_boxes)[0])
                y.append(class_dir)
                
                with open (csv_success, mode='a', newline='') as file:
                    writer = csv.writer(file)
                    now = datetime.now()
                    writer.writerow([img_counter, class_dir, img_path, now.strftime("%Y-%m-%d %H:%M:%S")])
                
                end_time_encoding = time.time()
                time_encoding = end_time_encoding - start_time_encoding
                total_time_encoding += time_encoding
                
                print(f"{folder_counter}. {class_dir}:",
                    f"File {img_counter}. {img_path} diproses. Waktu Encoding: {time_encoding:.2f} detik")
                
    # Determine how many neighbors to use for weighting in the KNN classifier
    if n_neighbors is None:
        n_neighbors = int(round(math.sqrt(len(X))))
        if verbose:
            print("Chose n_neighbors automatically:", n_neighbors)

    # Create and train the KNN classifier
    knn_clf = neighbors.KNeighborsClassifier(n_neighbors=n_neighbors, algorithm=knn_algo, weights='distance')
    knn_clf.fit(X, y)

    # Save the trained KNN classifier
    if model_save_path is not None:
        with open(model_save_path, 'wb') as f:
            pickle.dump(knn_clf, f)
            
    print(f"Folder diproses: {folder_counter}")
    print(f"Gambar diproses: {img_counter}")
    print(f"Total Waktu Encoding: {total_time_encoding:.2f} detik")
    print(f"Total Waktu Encoding: {total_time_encoding // 60:.0f} menit {total_time_encoding % 60:.0f} detik")
    print(f"Rata-Rata Waktu Encoding per Gambar: {total_time_encoding / img_counter:.2f} detik")
    print(f"Gambar yang gagal diproses: {failed_images_counter}")

    return knn_clf

if __name__ == "__main__":
    # Jika model ada, hapus dulu
    if os.path.exists(model_save_path):
        os.remove(model_save_path)
    
    # Membuat folder trained jika belum ada
    if not os.path.exists(fail_folder):
        os.makedirs(fail_folder)
        
    # Membuat CSV jika belum ada
    try:
        os.remove(csv_success)
    except:
        pass
    with open(csv_success, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['No.', 'Folder', 'File', 'Time'])
    
    # Membuat CSV jika belum ada
    try:
        os.remove(csv_fail)
    except:
        pass
    with open(csv_fail, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['No.', 'Folder', 'File', 'Information', 'Time'])
    
    print("Training KNN classifier...")
    train(train_dir = train_folder,
                    model_save_path = model_save_path,
                    n_neighbors = 2)
    print("Training complete!")
