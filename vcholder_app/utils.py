# -*- coding: utf-8 -*-
"""
    vcard_server.utils
    -----------------
    General utilities.
"""


import os
import base64
from vcholder_app import app, db, qr, lm
from vcholder_app.models import User, VCard
from flask import request, session, abort, flash
from functools import wraps


mimetypemap = {
    'gif': 'image/gif',
    'ico': 'image/vnd.microsoft.icon',
    'jpe': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'jpg': 'image/jpeg',
    'png': 'image/png',
}

TRUE_MAP = ['true', '1', 't', 'y', 'yes', 'Y', 'True', 'YES', 'show']


def get_avatar_file_name(uid):
    return '.'.join([uid, app.config['AVATAR_FILE_TYPE']])


def get_avatar_path(uid=None):
    if not uid:
        uid = app.config['DEFAULT_UUID']
    return os.path.join(app.root_path, 'avatars', get_avatar_file_name(uid))


def get_avatar_file_path(uid):
    if os.path.isfile(get_avatar_path(uid)):
        return get_avatar_path(uid)
    if os.path.isfile(get_avatar_path()):
        return get_avatar_path()
    return None


def get_mime_type_avatar():
    return mimetypemap[app.config['AVATAR_FILE_TYPE']]


def get_image(uid, attr='PHOTO'):
    file_name = '{}/avatars/{}.jpeg'.format(app.root_path, str(uid))
    if os.path.isfile(file_name):
        data = open(file_name, 'rb').read()
        return "{};TYPE=JPEG;ENCODING=b:{}".format(attr, base64.b64encode(data).decode())
    return None


def bool_request_arg(arg_name):
    if request.args.get(arg_name):
        session[arg_name] = request.args.get(arg_name)
    elif arg_name in session:
        return session[arg_name] in TRUE_MAP
    return request.args.get(arg_name) in TRUE_MAP


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in [app.config['AVATAR_FILE_TYPE'], 'jpg']


def secure_filename(filename):
    return filename


def update_user(user_id, username, password1, password2):
    obj_user = User.query.filter_by(id=user_id).first()
    if not obj_user or not username or username == '' or not password1 or password1 == '' or password1 != password2:
        flash('Update user error')
        return False
    obj_user.username = username
    obj_user.password = password1
    db.session.commit()
    return True


def get_headers_str(r):
    return str(r.headers).rstrip('\n\r')


def require_appkey(view_function):
    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        if request.headers.get('x-api-key') and User.query.filter_by(api_key=request.headers.get('x-api-key')).first():
            return view_function(*args, **kwargs)
        elif request.args.get('api-key') and User.query.filter_by(api_key=request.headers.get('x-api-key')).first():
            return view_function(*args, **kwargs)
        else:
            abort(401)
    return decorated_function
