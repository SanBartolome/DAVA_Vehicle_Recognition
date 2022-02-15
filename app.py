###############################################
#          Import some packages               #
###############################################
import ssl
import io
import glob
import requests
requests.packages.urllib3.disable_warnings()
import os
os.environ["KMP_DUPLICATE_LIB_OK"]="TRUE"
from flask import Flask, flash, redirect, url_for,render_template, request
from flask_bootstrap import Bootstrap
from flask_nav import Nav
from flask_nav.elements import *
from flask.helpers import send_file
from dominate.tags import img
from pytube import YouTube
from PIL import Image

###############################################
#          Define flask app                   #
###############################################
logo = img(src='./static/img/logo.jpg', height="50", width="50", style="margin-top:-15px")
topbar = Navbar(logo,
                View('Video', 'get_video'),
                View('Imagen', 'get_image'),
                )

# registers the "top" menubar
nav = Nav()
nav.register_element('top', topbar)

app = Flask(__name__)
Bootstrap(app)

app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

###############################################
#          Define variables                   #
###############################################

folder = os.path.join('static', 'uploads')
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4'}

###############################################
#          Define methods                     #
###############################################

def fetch(url):
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        # Legacy Python that doesn't verify HTTPS certificates by default
        pass
    else:
        # Handle target environment that doesn't support HTTPS verification
        ssl._create_default_https_context = _create_unverified_https_context

    try:
        yt = YouTube(url)
    except Exception:
        return -1
    else:
        return yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()

def remove_files():
    os.makedirs(folder, exist_ok=True)
    files = glob.glob(os.path.join(folder,'*'))
    for f in files:
	    os.remove(f)

def convert_rgb_to_jpg(filename, isUrl):
    if isUrl:
        response = requests.get(filename)
        im = Image.open(io.BytesIO(response.content))
    else:
        im = Image.open(os.path.join(folder, filename))
    rgb_im = im.convert('RGB')
    remove_files()
    rgb_im.save(os.path.join(folder, 'download.jpg'))

def save_image(file, isUrl):
    if isUrl:
        file_extension = file.rsplit('.')[-1].lower()
        if file_extension == 'png':
            convert_rgb_to_jpg(filename=file, isUrl=isUrl)
        else:
            response = requests.get(file)
            im = Image.open(io.BytesIO(response.content))
            remove_files()
            im.save(folder, 'download.jpg')
    else:
        file_extension = file.filename.rsplit('.')[-1].lower()
        if file_extension == 'png':
            convert_rgb_to_jpg(filename=file.filename, isUrl=isUrl)
        else:
            remove_files()
            file.save(os.path.join(folder, 'download.jpg'))

def allowed_image(filename):
    return '.' in filename and \
           filename.rsplit('.')[-1].lower() in ALLOWED_IMAGE_EXTENSIONS

def allowed_video(filename):
    return '.' in filename and \
           filename.rsplit('.')[-1].lower() in ALLOWED_VIDEO_EXTENSIONS

###############################################
#          Render pages                       #
###############################################
@app.route('/', methods=['GET', 'POST'])
def get_video():
    if request.method == 'POST':
        url_dw = request.form['url']
        if url_dw:
            y='https://www.youtube.com/watch'
            if y in url_dw:
                yt_file=fetch(url_dw)
                if yt_file==-1:
                    flash('No se puede acceder al video. Por favor, intente otro.')
                    return redirect(request.url)
                remove_files()
                yt_file.download(folder, 'download.mp4')
                return redirect(url_for('returnSuccess'))
            else:
                flash('El URL no es válido.')
                return redirect(request.url)
        file = request.files['file']
        if file:
            if allowed_video(file.filename):
                remove_files()
                file.save(os.path.join(folder, 'download.mp4'))
                return redirect(url_for('returnSuccess'))
            else:
                flash('Formato incorrecto. Subir un video con extensión mp4')
                return redirect(request.url)
        else:
            flash('Debe colocar un URL o subir un archivo.')
            return redirect(request.url)
    return render_template('video.html')

@app.route('/other', methods=["GET", "POST"])
def get_image():
    if request.method == 'POST':
        url_dw = request.form['url']
        if url_dw:
            if allowed_image(url_dw):
                save_image(url_dw, True)
                return redirect(url_for('returnSuccessOther'))
            else:
                flash('Formato incorrecto. El URL debe terminar en jpg o png.')
                return redirect(request.url)
        file = request.files['file']
        if file:
            if allowed_image(file.filename):
                save_image(file, False)
                return redirect(url_for('returnSuccessOther'))
            else:
                flash('Formato incorrecto. Subir una imagen con extensión jpg o png')
                return redirect(request.url)
        else:
            flash('Debe colocar un URL o subir un archivo.')
            return redirect(request.url)
    return(render_template('image.html'))

@app.route('/success', methods=["GET"])
def returnSuccess():
    return(render_template('success.html', filename="download.mp4"))

@app.route('/success-other', methods=["GET"])
def returnSuccessOther():
    return(render_template('success_other.html', filename="download.jpg"))

###############################################
#          Source routes                      #
###############################################

@app.route('/display/<filename>')
def display_video(filename):
    path_to_file = os.path.join(folder, filename)
    return send_file(
         path_to_file, 
         mimetype="video/mp4", 
         as_attachment=True, 
         attachment_filename=filename)

@app.route('/show/<filename>')
def display_image(filename):
    path_to_file = os.path.join(folder, filename)
    return send_file(
         path_to_file, 
         mimetype="image/jpeg", 
         as_attachment=True, 
         attachment_filename=filename)



nav.init_app(app)

###############################################
#                Run app                      #
###############################################
if __name__ == '__main__':
    app.run(debug=True)