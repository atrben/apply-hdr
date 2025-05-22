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

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

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
        # Ensure upload directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        print(f"Saving file to: {filepath}")
        try:
            file.save(filepath)
            print(f"File saved successfully: {filepath}")
            return jsonify({'filename': filename}), 200
        except Exception as e:
            print(f"Error saving file: {e}")
            return jsonify({'error': 'Failed to save file'}), 500
    return jsonify({'error': 'File type not allowed'}), 400

@app.route('/process', methods=['POST'])
def process_image():
    data = request.get_json()
    filename = data.get('filename')
    
    if not filename or not os.path.exists(os.path.join(UPLOAD_FOLDER, filename)):
        print(f"File not found or invalid filename: {filename}")
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
        # Check if magick is available
        magick_check = subprocess.run('magick -version', shell=True, text=True, capture_output=True)
        if magick_check.returncode == 0:
            print("ImageMagick is installed:", magick_check.stdout)
        else:
            print("ImageMagick not found or not working:", magick_check.stderr)
            # Fallback: Copy original file if ImageMagick is not available
            print("Falling back to copying original file without HDR effect")
            shutil.copy2(input_path, output_path)
            return jsonify({'processed_filename': output_filename})
        
        result = subprocess.run(command, shell=True, check=False, text=True, capture_output=True)
        if result.returncode != 0:
            print(f"ImageMagick command failed with return code {result.returncode}")
            print("ImageMagick command error:", result.stderr)
            print("ImageMagick command output:", result.stdout)
            # Fallback: Copy original file if processing fails
            print("Falling back to copying original file without HDR effect")
            shutil.copy2(input_path, output_path)
            return jsonify({'processed_filename': output_filename})
        else:
            print("ImageMagick command output:", result.stdout)
            if result.stderr:
                print("ImageMagick command error (non-fatal):", result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"ImageMagick processing failed (CalledProcessError): {e.stderr}")
        # Fallback: Copy original file if processing fails
        print("Falling back to copying original file without HDR effect")
        shutil.copy2(input_path, output_path)
        return jsonify({'processed_filename': output_filename})
    except FileNotFoundError as e:
        print(f"ImageMagick executable not found on system: {str(e)}")
        # Fallback: Copy original file if ImageMagick is not installed
        print("Falling back to copying original file without HDR effect")
        shutil.copy2(input_path, output_path)
        return jsonify({'processed_filename': output_filename})
    except Exception as e:
        print(f"Unexpected error during image processing: {str(e)}")
        # Fallback: Copy original file if any other error occurs
        print("Falling back to copying original file without HDR effect")
        shutil.copy2(input_path, output_path)
        return jsonify({'processed_filename': output_filename})
    
    # Check if temp file exists before copying
    if not os.path.exists(temp_brightened_path):
        print(f"Temporary file not found: {temp_brightened_path}")
        # Fallback: Copy original file if temp file not created
        print("Falling back to copying original file without HDR effect")
        shutil.copy2(input_path, output_path)
        return jsonify({'processed_filename': output_filename})
    
    # Save the processed image
    try:
        shutil.copy2(temp_brightened_path, output_path)
        print(f"Successfully copied {temp_brightened_path} to {output_path}")
        # Verify the output image
        output_img = Image.open(output_path)
        print(f"Output image dimensions: {output_img.size}, mode: {output_img.mode}")
    except Exception as e:
        print(f"Error copying file: {e}")
        # Fallback: Copy original file if copy fails
        print("Falling back to copying original file without HDR effect")
        shutil.copy2(input_path, output_path)
        return jsonify({'processed_filename': output_filename})
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
    full_path = os.path.join(app.config['PROCESSED_FOLDER'], filename)
    print(f"Attempting to serve file: {full_path}")
    if os.path.exists(full_path):
        print(f"File found, serving: {full_path}")
        return send_from_directory(app.config['PROCESSED_FOLDER'], filename, as_attachment=True)
    else:
        print(f"File not found: {full_path}")
        return jsonify({'error': 'File not found'}), 404

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port) 