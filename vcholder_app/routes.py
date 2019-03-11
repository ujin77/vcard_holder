from vcholder_app import app
from flask import jsonify
from flask import request
from flask import abort
from flask import Response
from functools import wraps
from vcholder_app.vcards import VCards


def require_appkey(view_function):
    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        # if request.args.get('key') and request.args.get('key') == app.config['API_KEY']:
        if request.headers.get('x-api-key') and request.headers.get('x-api-key') == app.config['API_KEY']:
            return view_function(*args, **kwargs)
        else:
            abort(401)
    return decorated_function


# @app.route('/')
@app.route('/index')
def index():
    return VCards().get_by_uid('00000000-0000-0000-0000-000000000000', True)


@app.route('/<string:uid>', methods=['GET'])
@app.route('/api/v1.0/get/<string:uid>', methods=['GET'])
def get_vcard(uid):
    if len(uid) == 0:
        abort(404)
    if not VCards().is_uid(uid):
        abort(404)
    headers = {'Content-Disposition': 'inline; filename="%s.vcf"' % uid}
    return Response(VCards().get_by_uid(uid), mimetype="text/x-vcard", headers=headers)


@app.route('/api/v1.0/gettext/<string:uid>', methods=['GET'])
def get_vcard_text(uid):
    if len(uid) == 0:
        abort(404)
    if not VCards().is_uid(uid):
        abort(404)
    return VCards().get_by_uid(uid, True)


@app.route('/api/v1.0/sync/<string:uid>', methods=['PUT'])
def sync_vcard(uid):
    if len(uid) == 0:
        abort(404)
    if not request.json:
        abort(400)
    (u, i) = VCards().ldap_sync(uid, request.json)
    # print(request.json)
    return jsonify({uid: {'updated': u, 'new': i}})


# @app.route('/<string:uid>', methods=['GET'])
@app.route('/api/v1.0/vcards/<string:uid>', methods=['GET'])
def get_vcard2(uid):
    if len(uid) == 0:
        abort(404)
    if not VCards().is_uid(uid):
        abort(404)
    if request.args.get('html'):
        return VCards().get_by_uid(uid, True)
    headers = {'Content-Disposition': 'inline; filename="%s.vcf"' % uid}
    return Response(VCards().get_by_uid(uid), mimetype="text/x-vcard", headers=headers)


@app.route('/api/v1.0/vcards/<string:uid>', methods=['PUT'])
@require_appkey
def add_vcard(uid):
    if len(uid) == 0:
        abort(404)
    if VCards().is_uid(uid):
        abort(409)
    VCards().ldap_sync(uid, request.json)
    return jsonify({uid: 'OK'})


@app.route('/api/v1.0/vcards/<string:uid>', methods=['DELETE'])
@require_appkey
def delete_vcard(uid):
    if len(uid) == 0:
        abort(404)
    if not VCards().is_uid(uid):
        abort(404)
    VCards().delete_by_uid(uid)
    return jsonify({uid: 'OK'})
