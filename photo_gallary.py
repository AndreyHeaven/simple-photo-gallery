import json
import mimetypes
import os
import random
from flask import Flask, render_template, request, Response
from flask.helpers import make_response
from flask.ext.cache import Cache
import zipstream
import zipfile

# from PIL import Image
# im = Image.open(image_filename)
# width, height = im.size

S = '983db650f7f79bc8e87d9a3ba418aefc'

app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})
ROOT_DIR = 'y:\\'
FILE_EXTS = ('.JPG')
# from werkzeug.contrib.cache import SimpleCache
# cache = SimpleCache()

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


@app.route('/folder_icon/<folder>/folder.jpg')
def folder_icon(folder):
    dirpath = os.path.join(ROOT_DIR, folder, S)
    if not os.path.exists(dirpath):
        return ''
    filenames = os.listdir(dirpath)
    f_name = random.choice(filenames)
    file = open(os.path.join(dirpath, f_name), 'rb')
    file_read = file.read()
    file.close()
    response = make_response(file_read)
    response.headers['Content-Type'] = mimetypes.guess_type(f_name)[0]
    response.headers['Content-Length'] = os.path.getsize(file.name)
    return response


@app.route('/th/<path:path>')
def get_file_thumbnail(path):
    real_path = os.path.join(ROOT_DIR, path)

    # dir_path = os.path.dirname(real_path)

    path_rindex = real_path.rindex('/')
    th_real_path = real_path[:path_rindex] + '/' + S + real_path[path_rindex:]
    if not os.path.exists(th_real_path):
        return make_response(None, 404)
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
def get_folder(path):
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
#     file = open(os.path.join(dirpath, file_name), 'rb')
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
