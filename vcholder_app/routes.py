from vcholder_app import app
from flask import jsonify
from flask import request
from flask import abort
from flask import Response

from vcholder_app.vcards import VCards


# @app.route('/')
@app.route('/index')
def index():
    return VCards().get_by_uid('00000000-0000-0000-0000-000000000000', True)


@app.route('/<string:uid>', methods=['GET'])
@app.route('/api/v1.0/get/<string:uid>', methods=['GET'])
def get_vcard(uid):
    # return VCards().get_by_uid(uid)
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
