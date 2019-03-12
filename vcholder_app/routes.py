from vcholder_app import app
from vcholder_app import db
from flask import render_template, url_for
from flask import jsonify
from flask import request
from flask import abort
from flask import Response
from functools import wraps
from vcholder_app.models import VCard


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


def render_vcf(items, uid):
    vcl = ['BEGIN:VCARD', 'VERSION:3.0']
    for vc_item in items:
        vcl.append('%s:%s' % (vc_item.vc_property, vc_item.vc_value))
    # vcl.append('UID:%s' % uid)
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


@app.route('/api/v1.0/sync/<string:uid>', methods=['PUT'])
def sync_vcard(uid):
    if len(uid) == 0:
        abort(404)
    if not request.json:
        abort(400)
    (u, i) = ldap_sync(uid, request.json)
    # print(request.json)
    return jsonify({uid: {'updated': u, 'new': i}})


@app.route('/<uuid(strict=False):uid>', methods=['GET'])
@app.route('/api/v1.0/vcards/<uuid(strict=False):uid>', methods=['GET'])
def get_card(uid):
    vcard_items = VCard.query.filter_by(uid=str(uid)).all()
    if not vcard_items:
        abort(404)
    if request.args.get('html'):
        return render_template('vcard.html', uid=str(uid),
                               vcard_items=vcard_items,
                               href=url_for('get_card', uid=str(uid)))
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
