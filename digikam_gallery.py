# -*- coding: utf-8 -*-
from StringIO import StringIO

__author__ = 'araigorodskiy'
import mimetypes
import random
from flask import Flask, render_template, request, Response, abort, send_file
from flask.helpers import make_response
from flask.ext.cache import Cache
import zipstream
from sqlalchemy.sql import and_, or_, not_
from flask.ext.sqlalchemy import SQLAlchemy
from os.path import expanduser
import os
from PIL import Image

DEFAULT_CACHE_TIMEOUT = 1 * 60 * 60

app = Flask(__name__)
home = expanduser('~/.simple-gallery/digikam4.db')
if not os.path.exists(os.path.dirname(home)):
    os.mkdir(os.path.dirname(home))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///%s' % home
# app.config['SQLALCHEMY_ECHO'] = True

db = SQLAlchemy(app)
cache = Cache(app, config={'CACHE_TYPE': 'filesystem','CACHE_DIR':os.path.join(os.path.dirname(home),'cache')})

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


@app.route('/<t>/<folder_id>/')
@cache.cached(timeout=DEFAULT_CACHE_TIMEOUT)
def files(t, folder_id):
    q = []
    if t == 'Albums':
        alb = Albums.query.get(folder_id)
        q = Images.get_by_album(folder_id)
    elif t == 'Peoples':
        alb = Tags.query.get(folder_id)
        q = Images.get_by_people_tag(folder_id)
    elif t == 'Best':
        alb = RATINGS[folder_id]
        if folder_id == 0:
            folder_id = -1
        q = Images.get_by_rating(folder_id)
    else:
        abort(400)
    return render_template('album.html', images=q, album=alb)


@app.route('/<t>/')
@cache.cached(timeout=DEFAULT_CACHE_TIMEOUT)
def albums(t):
    query = []
    if t == 'Albums':
        conditions = []
        for term in IGNORE_FOLDERS:
            conditions.append(Albums.relativePath.ilike(term))
        query = Albums.query.filter(and_(Albums.albumRoot_id > 0, not_(or_(*conditions))))
    elif t == 'Peoples':
        query = Tags.query.join(TagProperties, TagProperties.tagid == Tags.id) \
            .filter(TagProperties.property == 'kfaceId')
    elif t == 'Best':
        query = RATINGS
    else:
        abort(400)

    return render_template('albums.html',
                           rand=random.choice,
                           albums=query)


@app.route('/f/<image_id>/<image_name>')
@cache.cached(timeout=DEFAULT_CACHE_TIMEOUT)
def get_image(image_id, image_name):
    image = Images.query.get_or_404(image_id)
    path = image.get_specificPath()
    # file_io = open(path, 'rb')
    # file_read = file_io.read()
    # file_io.close()
    # response = make_response(file_read)
    # response.headers['Cache-Control'] = 'private, max-age=%d' % (60 * 60 * 24)
    # response.headers['Content-Type'] = mimetypes.guess_type(path)[0]
    # response.headers['Content-Length'] = os.path.getsize(file_io.name)
    # return response
    img = Image.open(path)
    i = 1200
    if img.size[0] > img.size[1]:
        aspect = img.size[1] / float(i)
        new_size = (int(img.size[0] / aspect), i)
    else:
        aspect = img.size[0] / float(i)
        new_size = (i, int(img.size[1] / aspect))
    img.resize(new_size, resample=Image.ANTIALIAS)
    img_io = StringIO()
    img.save(img_io, 'JPEG', quality=70)
    img_io.seek(0)
    return send_file(img_io, mimetype='image/jpeg', cache_timeout=(60 * 60 * 24))


def crop_to_square(img):
    width, height = img.size  # Get dimensions
    new_width, new_height = max(width, height), min(width, height)
    left = (width - new_height) / 2
    top = (height - new_height) / 2
    right = (width + new_height) / 2
    bottom = (height + new_height) / 2
    return img.crop((left, top, right, bottom))


def _get_thumb(image_id,h):
    image = Images.query.get_or_404(image_id)
    path = image.get_specificPath()
    img = Image.open(path)
    img = crop_to_square(img)
    img.thumbnail((h, h), resample=Image.NEAREST)
    img_io = StringIO()
    img.save(img_io, 'JPEG', quality=70)
    img_io.seek(0)
    return send_file(img_io, mimetype='image/jpeg', cache_timeout=(60 * 60 * 24))


@app.route('/th/<image_id>/<image_name>')
@cache.cached(timeout=DEFAULT_CACHE_TIMEOUT)
def get_thumb(image_id, image_name):
    return _get_thumb(image_id,100)
    # response = make_response(file_read)
    # response.headers['Cache-Control'] = 'private, max-age=%d' % (60 * 60 * 24)
    # response.headers['Content-Type'] = mimetypes.guess_type(real_path)[0]
    # response.headers['Content-Length'] = os.path.getsize(file_io.name)
    # return response




@app.route('/<t>/<album_id>/folder_icon.jpg')
@cache.cached(timeout=DEFAULT_CACHE_TIMEOUT)
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
    album_icon = album.icon
    if album is None or album_icon is None:
        if t == 'Albums':
            album_icon = Images.get_by_album(album_id).first()
        elif t == 'Peoples':
            album_icon = Images.get_by_people_tag(album_id).first()
        elif t == 'Best':
            album_icon = Images.get_by_rating(album_id).first()
        else:
            abort(404)
    if album_icon is None:
        return abort(404)
    return _get_thumb(album_icon.id, 200)


def zip_images(images):
    def generator():
        z = zipstream.ZipFile(mode='w', compression=zipstream.ZIP_STORED)
        for image in images:
            z.write(image.get_specificPath(), image.name)

        for chunk in z:
            yield chunk

    response = Response(generator(), mimetype='application/zip')
    response.headers['Content-Disposition'] = 'attachment; filename={}'.format('files.zip')
    return response


@app.route('/export.zip', methods=['get'])
def export():
    sel = request.args.get('ids', '')
    sel = sel.split(',')
    if len(sel) == 0 or sel[0] == '':
        abort(400)
    images = Images.query.filter(Images.id.in_(sel))
    return zip_images(images)

@app.route('/<t>/<folder_id>/export.zip')
@cache.cached(timeout=DEFAULT_CACHE_TIMEOUT)
def export_album(t,folder_id):
    q = []
    if t == 'Albums':
        q = Images.get_by_album(folder_id)
    elif t == 'Peoples':
        q = Images.get_by_people_tag(folder_id)
    elif t == 'Best':
        if folder_id == 0:
            folder_id = -1
        q = Images.get_by_rating(folder_id)
    else:
        abort(400)
    return zip_images(q)


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0')

