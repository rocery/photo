from flask import Flask, render_template, Response, jsonify, request, redirect, url_for, flash, session
import csv
import os
from uploads import *

app = Flask(__name__)
app.secret_key = 'itbekasioke'
app.config['UPLOAD_FOLDER'] = 'img/raw'

csv_data_photo_uploaded = 'img/photo_uploaded.csv'
USER_SECRET_KEY = "user123"

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
    
if not os.path.exists(csv_data_photo_uploaded):
    with open(csv_data_photo_uploaded, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Photo_Path', 'Time_Upload'])
        
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        secret_key = request.form.get('secret_key')
        if secret_key == USER_SECRET_KEY:
            session['authenticated'] = True
            return redirect(url_for('index'))
        else:
            flash('Password salah, silahkan coba kembali.', 'danger')
    
    return render_template('login.html')
        
@app.route('/', methods=['GET', 'POST'])
def index():
    if not session.get('authenticated'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        nip = request.form['nip']
        name = request.form['name']
        images = request.files.getlist('images')
        
        # Input Validation
        if not name or not nip or not images:
            flash('Mohon isi semua form', 'danger')
            return redirect(request.url)
        
        if not "".join(name.split()).isalpha():
            flash('Nama harus berupa huruf', 'danger')
            return redirect(request.url)

        if not nip.isdigit():
            flash('NIP harus berupa angka', 'danger')
            return redirect(request.url)
        
        # Validasi format gambar
        for image in images:
            if not allowed_file(image.filename):
                flash('Format gambar harus JPG, JPEG, atau PNG', 'danger')
                return redirect(request.url)

        formatted_name = format_name(name)
        folder_name = f"{formatted_name}_{nip}"
        folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder_name)
        
        save_image(images, folder_path)
        flash('Data {} berhasil disimpan'.format(folder_name), 'success')
        return redirect(request.url)
    
    folders_info = get_folders_info(app.config['UPLOAD_FOLDER'])
    return render_template('index.html', folders_info=folders_info) 
        
if __name__ == '__main__':
    # if debug True, camera only run once then blank or in another word: Error
    app.run(host='0.0.0.0', port=5001, threaded=True)
