# -*- coding: utf-8 -*-
from StringIO import StringIO

__author__ = 'araigorodskiy'
import json
import mimetypes
import os
import random
from flask import Flask, render_template, request, Response, abort, send_file
from flask.helpers import make_response
from flask.ext.cache import Cache
import zipstream
from flask.ext.sqlalchemy import SQLAlchemy

from PIL import Image

app = Flask(__name__)
ROOT_DIR = u'/home/araigorodskiy/Изображения'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///%s/digikam4.db' % ROOT_DIR
app.config['SQLALCHEMY_ECHO'] = True

db = SQLAlchemy(app)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

from model import *


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


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/<t>/<int:tag_id>/')
def peoples_files(t, tag_id):
    q = []
    if t == 'Albums':
        q = Images.query.filter(Images.album_id == tag_id)
    elif t == 'Peoples':
        q = Images.query.join(ImageTags, ImageTags.imageid == Images.id).filter(ImageTags.tagid == tag_id)
    elif t == 'Best':
        if tag_id == 0: tag_id = -1
        q = Images.query.join(ImageInformation, ImageInformation.imageid == Images.id).filter(
            ImageInformation.rating == tag_id).filter(Images.status == 1)
    else:
        abort(400)
    return render_template('album.html', images=q)


@app.route('/<t>/')
def albums(t):
    query = []
    if t == 'Albums':
        query = Albums.query.filter(Albums.albumRoot_id > 0)
    elif t == 'Peoples':
        query = Tags.query.join(TagProperties, TagProperties.tagid == Tags.id) \
            .filter(TagProperties.property == 'kfaceId')
    elif t == 'Best':
        query = [
            Ratings(0, u'Без оценки'),
            Ratings(1, u'1'),
            Ratings(2, u'2'),
            Ratings(3, u'3'),
            Ratings(4, u'4'),
            Ratings(5, u'5'),
        ]
    else:
        abort(400)

    return render_template('albums.html',
                           rand=random.choice,
                           albums=query)


@app.route('/f/<type>/<album_id>/<image_id>/<image_name>')
@cache.cached(timeout=1 * 60 * 60)
def get_image(type, album_id, image_id, image_name):
    image = Images.query.get_or_404(image_id)
    path = image.get_specificPath()
    file_io = open(path, 'rb')
    file_read = file_io.read()
    file_io.close()
    response = make_response(file_read)
    response.headers['Cache-Control'] = 'private, max-age=%d' % (60 * 60 * 24)
    response.headers['Content-Type'] = mimetypes.guess_type(path)[0]
    response.headers['Content-Length'] = os.path.getsize(file_io.name)
    return response


@app.route('/th/<album_id>/<image_id>/<image_name>')
# @cache.cached(timeout=1 * 60 * 60)
def get_thumb(album_id, image_id, image_name):
    image = Images.query.get_or_404(image_id)
    path = image.get_specificPath()
    image_open = Image.open(path)
    image_open.thumbnail((280, 280), resample=Image.ANTIALIAS)
    img_io = StringIO()
    image_open.save(img_io, 'JPEG', quality=70)
    img_io.seek(0)
    return send_file(img_io, mimetype='image/jpeg')
    # response = make_response(file_read)
    # response.headers['Cache-Control'] = 'private, max-age=%d' % (60 * 60 * 24)
    # response.headers['Content-Type'] = mimetypes.guess_type(real_path)[0]
    # response.headers['Content-Length'] = os.path.getsize(file_io.name)
    # return response


@app.route('/<t>/<album_id>/folder_icon.jpg')
def folder_icon(t, album_id):
    album = None
    if t == 'Albums':
        album = Albums.query.get(album_id)
    elif t == 'Peoples':
        album = Tags.query.get(album_id)
    elif t == 'Best':
        album = Tags.query.get(album_id)
    else:
        abort(404)
    if album is None or album.icon is None:
        return send_file(open(os.path.join(os.path.dirname(__file__), 'no-image.jpg')))
    return get_thumb(None, album.icon.id, album.icon.name)

@app.route('/export.zip', methods=['get'])
def export():
    # sel = json.loads(request.form.get('selected'))
    sel = request.args.get('ids', '')
    sel = sel.split(',')
    def generator():
        z = zipstream.ZipFile(mode='w', compression=zipstream.ZIP_DEFLATED)
        for j in sel:
            image = Images.query.get(j)
            z.write(image.get_specificPath(), image.name)

        for chunk in z:
            yield chunk

    response = Response(generator(), mimetype='application/zip')
    response.headers['Content-Disposition'] = 'attachment; filename={}'.format('files.zip')
    return response

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0')

