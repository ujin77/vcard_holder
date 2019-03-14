import os
import io
from vcholder_app import app
from vcholder_app import db, qrcode
from flask import render_template, url_for, send_file
from flask import jsonify, request, abort, Response
from functools import wraps
from vcholder_app.models import VCard
import base64

mimetypemap = {
    'gif': 'image/gif',
    'ico': 'image/vnd.microsoft.icon',
    'jpe': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'jpg': 'image/jpeg',
    'png': 'image/png',
}


def require_appkey(view_function):
    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        if request.headers.get('x-api-key') and request.headers.get('x-api-key') == app.config['API_KEY']:
            return view_function(*args, **kwargs)
        elif request.args.get('api-key') and request.args.get('api-key') == app.config['API_KEY']:
            return view_function(*args, **kwargs)
        else:
            abort(401)
    return decorated_function


def ldap_sync(uid, data):
    updated = 0
    inserted = 0
    for vc_property in data:
        vcard = VCard.query.filter_by(uid=uid, vc_property=vc_property).first()
        if vcard:
            if vcard.vc_value != data[vc_property]:
                # print('Update: [%s] [%s]' % (vcard.vc_value, data[vc_property]))
                vcard.vc_value = data[vc_property]
                updated += 1
        else:
            db.session.add(VCard(uid, vc_property, data[vc_property]))
            inserted += 1
            # print('Insert')
    db.session.commit()
    return updated, inserted


def get_image(uid, attr='PHOTO'):
    file_name = '{}/avatars/{}.jpeg'.format(app.root_path, str(uid))
    if os.path.isfile(file_name):
        data = open(file_name, 'rb').read()
        return "{};TYPE=JPEG;ENCODING=b:{}".format(attr, base64.b64encode(data).decode())
    return None


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


def render_vcf(items, uid):
    vcl = ['BEGIN:VCARD', 'VERSION:3.0']
    avatar = get_image(str(uid), 'PHOTO')
    if not avatar:
        avatar = get_image(app.config['DEFAULT_UUID'], 'PHOTO')
    for vc_item in items:
        vcl.append('%s:%s' % (vc_item.vc_property, vc_item.vc_value))
    if avatar:
        vcl.append(avatar)
    vcl.append('UID:%s' % uid)
    vcl.append('END:VCARD')
    headers = {'Content-Disposition': 'inline; filename="%s.vcf"' % str(uid)}
    return Response("\n".join(vcl), mimetype="text/x-vcard", headers=headers)


# def render_qrcode(items, uid):
#     vcl = ['BEGIN:VCARD', 'VERSION:3.0']
#     for vc_item in items:
#         vcl.append('%s:%s' % (vc_item.vc_property, vc_item.vc_value))
#     vcl.append('UID:%s' % uid)
#     vcl.append('END:VCARD')
#     return send_file(qrcode("\n".join(vcl), mode='raw'), mimetype='image/png')


@app.route('/index')
def index():
    uid = app.config['DEFAULT_UUID']
    items = VCard.query.filter_by(uid=uid).all()
    if not items:
        abort(404)
    return render_template('vcard.html', uid=uid, vcard_items=items)


@app.route('/api/v1.0/sync/<uuid(strict=False):uid>', methods=['PUT'])
@require_appkey
def sync_vcard(uid):
    if not request.json:
        abort(400)
    (u, i) = ldap_sync(str(uid), request.json)
    # print(request.json)
    return jsonify({str(uid): {'updated': u, 'new': i}})


@app.route('/<uuid(strict=False):uid>', methods=['GET'])
@app.route('/api/v1.0/vcards/<uuid(strict=False):uid>', methods=['GET'])
def get_card(uid):
    vcard_items = VCard.query.filter_by(uid=str(uid)).all()
    if not vcard_items:
        abort(404)
    if request.args.get('html'):
        return render_template('vcard.html', uid=str(uid), vcard_items=vcard_items)
    return render_vcf(vcard_items, str(uid))


@app.route('/api/v1.0/vcards/<uuid(strict=False):uid>', methods=['PUT'])
@require_appkey
def add_card(uid):
    if VCard.query.filter_by(uid=str(uid)).first():
        abort(409)
    ldap_sync(str(uid), request.json)
    return jsonify({uid: 'OK'})


@app.route('/api/v1.0/vcards/<uuid(strict=False):uid>', methods=['DELETE'])
@require_appkey
def delete_card(uid):
    vcards = VCard.query.filter_by(uid=str(uid)).all()
    if not vcards:
        abort(404)
    for vcard in vcards:
        db.session.delete(vcard)
    db.session.commit()
    return jsonify({str(uid): 'DELETED'})


@app.route('/api/v1.0/avatars/<uuid(strict=False):uid>', methods=['GET'])
def get_avatar(uid):
    file_name = get_avatar_file_path(str(uid))
    if file_name:
        with open(file_name, 'rb') as bites:
            return send_file(io.BytesIO(bites.read()), attachment_filename=get_avatar_file_name(str(uid)),
                             mimetype=mimetypemap[app.config['AVATAR_FILE_TYPE']])
    abort(404)


@app.route('/api/v1.0/qrcode/<uuid(strict=False):uid>', methods=['GET'])
def get_qrcode(uid):
    vcard_items = VCard.query.filter_by(uid=str(uid)).all()
    if not vcard_items:
        abort(404)
    return send_file(qrcode(url_for('get_card', uid=str(uid), _external=True), mode='raw'), mimetype='image/png')
