import json
import mimetypes
import os
import random
from flask import Flask, render_template, request, Response, abort
from flask.helpers import make_response
from flask.ext.cache import Cache
import zipstream

from PIL import Image
# im = Image.open(image_filename)
# width, height = im.size

S = '983db650f7f79bc8e87d9a3ba418aefc'

app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})
ROOT_DIR = 'E:\\'
FILE_EXTS = ('.JPG')
# from werkzeug.contrib.cache import SimpleCache
# cache = SimpleCache()

@app.route('/css/css.css')
# @cache.cached(timeout=1*60*60)
def css():
    def generate():
        from random import choice as rand

        classs = range(11)
        pxx = range(-10, 11, 2)
        degs = range(-10, 11, 2)
        for item in classs:
            deg = rand(degs)
            yield '.folder_%s:before {\n' % item
            yield '    top: %spx;\n' % rand(pxx)
            yield '    left: %spx;\n' % rand(pxx)
            yield '    -webkit-transform: rotate(%sdeg);\n' % deg
            yield '    -moz-transform: rotate(%sdeg);\n' % deg
            yield '    -o-transform: rotate(%sdeg);\n' % deg
            yield '    -ms-transform: rotate(%sdeg);\n' % deg
            yield '    transform: rotate(%sdeg);\n' % deg
            yield '}\n'
            deg = rand(degs)
            yield '.folder_%s:after {\n' % item
            yield '    top: %spx;\n' % rand(pxx)
            yield '    left: %spx;\n' % rand(pxx)
            yield '    -webkit-transform: rotate(%sdeg);\n' % deg
            yield '    -moz-transform: rotate(%sdeg);\n' % deg
            yield '    -o-transform: rotate(%sdeg);\n' % deg
            yield '    -ms-transform: rotate(%sdeg);\n' % deg
            yield '    transform: rotate(%sdeg);\n' % deg
            yield '}\n'

    return Response(generate(), mimetype='text/css')


@app.route('/export.zip', methods=['POST'])
def export():
    sel = json.loads(request.form.get('selected'))

    def generator():
        z = zipstream.ZipFile(mode='w', compression=zipstream.ZIP_DEFLATED)
        for j in sel:
            z.write(os.path.join(ROOT_DIR, j))

        for chunk in z:
            yield chunk

    response = Response(generator(), mimetype='application/zip')
    response.headers['Content-Disposition'] = 'attachment; filename={}'.format('files.zip')
    return response


@app.route('/folder_icon/<path:folder>/folder.jpg')
# @cache.cached(timeout=1*60*60)
def folder_icon(folder):
    dirpath = os.path.join(ROOT_DIR, folder, S)
    f_name = None
    if os.path.exists(dirpath):
        filenames = os.listdir(dirpath)
        f_name = random.choice(filenames)
    if f_name == None:
        f_name = 'no-image.jpg'
        dirpath = os.path.dirname(__file__)
    path_join = os.path.join(dirpath, f_name)
    file = open(path_join, 'rb')
    file_read = file.read()
    file.close()
    response = make_response(file_read)
    response.headers['Content-Type'] = mimetypes.guess_type(f_name)[0]
    response.headers['Content-Length'] = os.path.getsize(file.name)
    return response


@app.route('/th/<path:path>')
@cache.cached(timeout=1 * 60 * 60)
def get_file_thumbnail(path):
    real_path = os.path.join(ROOT_DIR, path)
    path_rindex = real_path.rindex('/')
    th_real_path = real_path[:path_rindex] + '/' + S + real_path[path_rindex:]
    if not os.path.exists(th_real_path):
        image_open = Image.open(real_path)
        image_open.thumbnail((280, 280), resample=Image.ANTIALIAS)
        path_dirname = os.path.dirname(th_real_path)
        if not os.path.exists(path_dirname):
            os.mkdir(path_dirname)
        image_open.save(th_real_path)
        # th_real_path = real_path
    file = open(th_real_path, 'rb')
    file_read = file.read()
    file.close()
    response = make_response(file_read)
    response.headers['Cache-Control'] = 'private, max-age=%d' % (60 * 60 * 24)
    response.headers['Content-Type'] = mimetypes.guess_type(th_real_path)[0]
    response.headers['Content-Length'] = os.path.getsize(file.name)
    return response


def create_breadcrumb(path):
    br = []
    res = []
    for p in path.split('/'):
        if p:
            br.append(p)
            res.append((p, '/' + '/'.join(br)))
    return res


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
# @cache.cached(timeout=1*60*60)
def get_folder_or_file(path):
    real_path = os.path.join(ROOT_DIR, path)
    if os.path.isdir(real_path):
        breadcrumb = create_breadcrumb(path)
        children = os.listdir(real_path)
        files = []
        folders = []
        for c in children:
            if os.path.isdir(os.path.join(real_path, c)):
                folders.append(c)
            else:
                files.append(c)
        files_filter = lambda s: not s.startswith('.') \
                                 and s.upper().endswith(FILE_EXTS)
        dirs_filter = lambda s: not s.startswith('.') \
                                and s != S
        files = filter(files_filter, files)
        files = sorted(files)
        folders = filter(dirs_filter, folders)
        folders = sorted(folders)
        return render_template('files.html', folder=path, breadcrumb=breadcrumb, folders=folders, files=files,
                               rand=random.choice)
    else:
        file = open(real_path, 'rb')
        file_read = file.read()
        file.close()
        response = make_response(file_read)
        response.headers['Cache-Control'] = 'private, max-age=%d' % (60 * 60 * 24)
        response.headers['Content-Type'] = mimetypes.guess_type(real_path)[0]
        response.headers['Content-Length'] = os.path.getsize(file.name)
        return response

# @app.route('/files/<folder_name>/<file_name>')
# def get_file_content(folder_name, file_name):
# dirpath = os.path.join(ROOT_DIR, folder_name)
# file = open(os.path.join(dirpath, file_name), 'rb')
#     file_read = file.read()
#     file.close()
#     response = make_response(file_read)
#     response.headers['Cache-Control'] = 'private, max-age=%d' % (60 * 60 * 24)
#     response.headers['Content-Type'] = mimetypes.guess_type(file_name)[0]
#     response.headers['Content-Length'] = os.path.getsize(file.name)
#     return response



if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0')
