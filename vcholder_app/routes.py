from vcholder_app import app
from flask import jsonify
from flask import request
from flask import abort
from flask import Response

from vcholder_app.vcards import VCards


@app.route('/')
@app.route('/index')
def index():
    return VCards().get_by_uid('00000000-0000-0000-0000-000000000000', True)


@app.route('/api/v1.0/notification/<string:notify_event>', methods=['GET'])
def get_notification(notify_event):
    if notify_event == 'workflow':
        jobId = request.args.get('jobId', default='*', type=str)
        status = request.args.get('status', default='*', type=str)
        parentId = request.args.get('parentId', default='*', type=str)
        print("%s: [%s] [%s] [%s]" % (notify_event, jobId, parentId, status))
    elif notify_event == 'action':
        jobId = request.args.get('jobId', default='*', type=str)
        nodeName = request.args.get('nodeName', default='*', type=str)
        status = request.args.get('status', default='*', type=str)
        print("%s: [%s] [%s] [%s]" % (notify_event, jobId, nodeName, status))
    else:
        print(notify_event)
    return jsonify({'result': 'OK'})


@app.route('/api/v1.0/get/<string:uid>', methods=['GET'])
def get_vcard(uid):
    # return VCards().get_by_uid(uid)
    headers = {'Content-Disposition': 'inline; filename="%s.vcf"' % uid}
    return Response(VCards().get_by_uid(uid), mimetype="text/x-vcard", headers=headers)


@app.route('/api/v1.0/gettext/<string:uid>', methods=['GET'])
def get_vcard_text(uid):
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
