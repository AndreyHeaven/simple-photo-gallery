import os
from digikam_gallery import db

__author__ = 'araigorodskiy'

class AlbumRoots(db.Model):
    __tablename__ = 'AlbumRoots'
    id = db.Column(db.Integer, primary_key=True)
    specificPath = db.Column(db.Text())


class Albums(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # albumRoot = db.relationship("Albums", foreign_keys=[albumRoot_id])
    relativePath = db.Column(db.Text())
    icon_id = db.Column('icon', db.Integer, db.ForeignKey('images.id'))
    albumRoot_id = db.Column('albumRoot', db.Integer, db.ForeignKey(AlbumRoots.id))
    albumRoot = db.relationship("AlbumRoots", backref="children", remote_side=AlbumRoots.id)

    def get_link(self):
        return '%d/' % self.id

    def get_name(self):
        return self.relativePath[1:]

    def get_path(self):
        return '%s%s' %(self.albumRoot.specificPath, self.relativePath)




class Images(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text())
    status = db.Column(db.Integer)
    album_id = db.Column('album', db.Integer, db.ForeignKey('albums.id'))
    album = db.relationship("Albums", backref="images", remote_side=Albums.id, foreign_keys=[album_id])

    def get_relativePath(self):
        return self.album.relativePath + '/' + self.name

    def get_specificPath(self):
        return self.album.albumRoot.specificPath + self.album.relativePath + '/' + self.name

    def get_path_with_ids(self):
        return '%d/%d/%s' % (self.album.id, self.id, self.name)

    def get_file(self):
        return open(self.get_specificPath())

Albums.icon = db.relationship("Images", backref="images", remote_side=Images.id, foreign_keys=[Albums.icon_id])


class Tags(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text())
    pid = db.Column(db.Integer)
    icon_id = db.Column('icon', db.Integer, db.ForeignKey('images.id'))
    icon = db.relationship("Images", backref="tags", remote_side=Images.id, foreign_keys=[icon_id])

    def get_link(self):
        return '%d/' % self.id

    def get_name(self):
        return self.name


class TagProperties(db.Model):
    __tablename__ = 'TagProperties'
    tagid = db.Column(db.Integer, db.ForeignKey('tags.id'), primary_key=True)
    property = db.Column(db.Text(), primary_key=True)
    value = db.Column(db.Text())


class ImageTags(db.Model):
    __tablename__ = 'ImageTags'
    imageid = db.Column(db.Integer, db.ForeignKey('images.id'), primary_key=True)
    tagid = db.Column(db.Integer, db.ForeignKey('tags.id'), primary_key=True)


class ImageInformation(db.Model):
    __tablename__ = 'ImageInformation'
    imageid = db.Column(db.Integer, db.ForeignKey('images.id'), primary_key=True)
    rating = db.Column(db.Integer)


class Ratings():
    def __init__(self, rating, name):
        self.rating = rating
        self.name = name

    def get_link(self):
        return '%d/' % self.rating

    def get_name(self):
        return self.name
