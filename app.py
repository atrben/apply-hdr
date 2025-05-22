# app.py
# Flask application for HDR Emoji Maker

from flask import Flask, render_template, request, send_from_directory, jsonify
import os
import subprocess
import numpy as np
from werkzeug.utils import secure_filename
from PIL import Image, ImageDraw
import shutil

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads'
PROCESSED_FOLDER = 'static/processed'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return jsonify({'filename': filename}), 200
    return jsonify({'error': 'File type not allowed'}), 400

@app.route('/process', methods=['POST'])
def process_image():
    data = request.get_json()
    filename = data.get('filename')
    
    if not filename or not os.path.exists(os.path.join(UPLOAD_FOLDER, filename)):
        return jsonify({'error': 'File not found'}), 404
    
    input_path = os.path.join(UPLOAD_FOLDER, filename)
    output_filename = f"processed_HDR_{filename}"
    output_path = os.path.join(PROCESSED_FOLDER, output_filename)
    
    icc_profile_path = os.path.join('assets', 'Profile ICC 2020.icc')
    if os.path.exists(icc_profile_path):
        icc_profile = f'-profile "{icc_profile_path}"'
        note = "HDR effect applied with ICC profile."
    else:
        icc_profile = ''
        note = "HDR effect applied. Note: For full HDR effect, ensure 'Profile ICC 2020.icc' is in the 'assets' directory."
    print(note)
    
    temp_brightened_path = os.path.join(UPLOAD_FOLDER, f"brightened_{filename}")
    command = (
        f'magick "{input_path}" '
        f'-define quantum:format=floating-point '
        f'-colorspace RGB '
        f'-auto-gamma '
        f'-evaluate Multiply 1.5 '
        f'-evaluate Pow 0.9 '
        f'-colorspace sRGB '
        f'-depth 16 '
        f'{icc_profile} "{temp_brightened_path}"'
    )
    print(f"Executing command: {command}")
    try:
        result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
        print("ImageMagick command output:", result.stdout)
        if result.stderr:
            print("ImageMagick command error:", result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"ImageMagick processing failed: {e.stderr}")
        return jsonify({'error': 'Processing failed'}), 500
    
    # Check if temp file exists before copying
    if not os.path.exists(temp_brightened_path):
        print(f"Temporary file not found: {temp_brightened_path}")
        return jsonify({'error': 'Processing failed, temporary file not created'}), 500
    
    # Save the processed image
    try:
        shutil.copy2(temp_brightened_path, output_path)
        print(f"Successfully copied {temp_brightened_path} to {output_path}")
        # Verify the output image
        output_img = Image.open(output_path)
        print(f"Output image dimensions: {output_img.size}, mode: {output_img.mode}")
    except Exception as e:
        print(f"Error copying file: {e}")
        return jsonify({'error': 'Processing failed during file copy'}), 500
    finally:
        try:
            if os.path.exists(temp_brightened_path):
                os.remove(temp_brightened_path)
                print(f"Successfully removed temporary file: {temp_brightened_path}")
        except Exception as e:
            print(f"Error removing temporary file: {e}")
    
    return jsonify({'processed_filename': output_filename})

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['PROCESSED_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port) 
