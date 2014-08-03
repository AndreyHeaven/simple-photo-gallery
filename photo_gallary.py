import mimetypes
import os
import random
from flask import Flask, render_template
from flask.helpers import make_response

S = '983db650f7f79bc8e87d9a3ba418aefc'

app = Flask(__name__)
ROOT_DIR = 'z:\\'
FILE_EXTS = ('.JPG')
from werkzeug.contrib.cache import SimpleCache
cache = SimpleCache()
@app.route('/')
def hello_world():
    os_listdir = os.listdir(ROOT_DIR)
    os_listdir = filter(lambda s: os.path.isdir(os.path.join(ROOT_DIR, s)), os_listdir)
    return render_template("app.html", dirnames=sorted(os_listdir), rand=random.choice)


@app.route('/folder_icon/<folder>.jpg')
def folder_icon(folder):
    dirpath = os.path.join(ROOT_DIR, folder, S)
    filenames = os.listdir(dirpath)
    f_name = random.choice(filenames)
    file = open(os.path.join(dirpath, f_name), 'rb')
    file_read = file.read()
    file.close()
    response = make_response(file_read)
    response.headers['Content-Type'] = mimetypes.guess_type(f_name)[0]
    response.headers['Content-Length'] = os.path.getsize(file.name)
    return response

@app.route('/<folder>')
def get_folder(folder):
    os_listdir = cache.get(folder)
    if os_listdir is None:
        os_listdir = os.listdir(os.path.join(ROOT_DIR,folder))
        startswith___ = lambda s: os.path.isfile(os.path.join(ROOT_DIR, folder, s)) and not s.startswith('.') and s.upper().endswith(FILE_EXTS)
        os_listdir = filter(startswith___, os_listdir)
        os_listdir = sorted(os_listdir)
        cache.set(folder, os_listdir, timeout=5*60)
    return render_template('files.html', folder=folder, files=os_listdir)

@app.route('/files/<folder_name>/<file_name>')
def get_file_content(folder_name, file_name):
    dirpath = os.path.join(ROOT_DIR, folder_name)
    file = open(os.path.join(dirpath, file_name), 'rb')
    file_read = file.read()
    file.close()
    response = make_response(file_read)
    response.headers['Cache-Control'] = 'private, max-age=%d' % (60 * 60 * 24)
    response.headers['Content-Type'] = mimetypes.guess_type(file_name)[0]
    response.headers['Content-Length'] = os.path.getsize(file.name)
    return response


@app.route('/thumbnails/<folder_name>/<file_name>')
def get_file_thumbnail(folder_name, file_name):
    dirpath = os.path.join(ROOT_DIR, folder_name, S)
    file = open(os.path.join(dirpath, file_name), 'rb')
    file_read = file.read()
    file.close()
    response = make_response(file_read)
    response.headers['Cache-Control'] = 'private, max-age=%d' % (60 * 60 * 24)
    response.headers['Content-Type'] = mimetypes.guess_type(file_name)[0]
    response.headers['Content-Length'] = os.path.getsize(file.name)
    return response


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0')
