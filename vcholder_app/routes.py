import os
import io
from vcholder_app import app
from vcholder_app import db
from flask import render_template, url_for, send_file
from flask import jsonify, request, abort, Response
from functools import wraps
from vcholder_app.models import VCard
import base64


def require_appkey(view_function):
    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        # if request.args.get('key') and request.args.get('key') == app.config['API_KEY']:
        if request.headers.get('x-api-key') and request.headers.get('x-api-key') == app.config['API_KEY']:
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


def url_photo(uid):
    if os.path.isfile('{}/avatars/{}.jpeg'.format(app.root_path, str(uid))):
        return url_for('get_avatar', uid=str(uid))
    elif os.path.isfile('{}/avatars/00000000-0000-0000-0000-000000000000.jpeg'.format(app.root_path)):
        return url_for('get_avatar', uid='00000000-0000-0000-0000-000000000000')
    return None


def get_image(uid, attr='PHOTO'):
    file_name = '{}/avatars/{}.jpeg'.format(app.root_path, str(uid))
    if os.path.isfile(file_name):
        data = open(file_name, 'rb').read()
        return "{};TYPE=JPEG;ENCODING=b:{}".format(attr, base64.b64encode(data).decode())
    return None


def render_vcf(items, uid):
    vcl = ['BEGIN:VCARD', 'VERSION:3.0']
    avatar = get_image(str(uid), 'PHOTO')
    if not avatar:
        avatar = get_image('00000000-0000-0000-0000-000000000000', 'PHOTO')
    for vc_item in items:
        vcl.append('%s:%s' % (vc_item.vc_property, vc_item.vc_value))
    if avatar:
        vcl.append(avatar)
    vcl.append('UID:%s' % uid)
    vcl.append('END:VCARD')
    headers = {'Content-Disposition': 'inline; filename="%s.vcf"' % str(uid)}
    return Response("\n".join(vcl), mimetype="text/x-vcard", headers=headers)


@app.route('/index')
def index():
    uid = '00000000-0000-0000-0000-000000000000'
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
        return render_template('vcard.html', uid=str(uid),
                               vcard_items=vcard_items,
                               href=url_for('get_card', uid=str(uid)),
                               photo=url_photo(str(uid)))
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
    return jsonify({uid: 'OK'})


@app.route('/api/v1.0/avatars/<uuid(strict=False):uid>', methods=['GET'])
def get_avatar(uid):
    file_name = '{}/avatars/{}.jpeg'.format(app.root_path, str(uid))
    if os.path.isfile(file_name):
        with open(file_name, 'rb') as bites:
            return send_file(io.BytesIO(bites.read()), attachment_filename='{}.jpeg'.format(str(uid)),
                             mimetype='image/jpg')
    abort(404)
