import os
import io
from vcholder_app import app, db, qrcode, login_manager
from flask import render_template, url_for, send_file
from flask import jsonify, request, abort, Response, flash, redirect, send_from_directory
from functools import wraps
from vcholder_app.models import VCard, User
import base64
from shortuuid import encode as suuid_encode
from shortuuid import decode as suuid_decode
import flask_login


mimetypemap = {
    'gif': 'image/gif',
    'ico': 'image/vnd.microsoft.icon',
    'jpe': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'jpg': 'image/jpeg',
    'png': 'image/png',
}

TRUE_MAP = ['true', '1', 't', 'y', 'yes', 'Y', 'True', 'YES', 'show']


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
        # if vc_item.vc_property[:2] == 'FN':
        #     print(vc_item.vc_value)
    if avatar:
        vcl.append(avatar)
    vcl.append('UID:%s' % uid)
    vcl.append('END:VCARD')
    # headers = {'Content-Disposition': 'inline; filename="%s.vcf"' % str(uid)}
    # return Response("\n".join(vcl), mimetype="text/x-vcard", headers=headers)
    return Response("\n".join(vcl), content_type="text/x-vcard")


def bool_request_arg(arg_name):
    return request.args.get(arg_name) in TRUE_MAP


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in [app.config['AVATAR_FILE_TYPE'], 'jpg']


def secure_filename(filename):
    return filename


def update_user(id, username, password1, password2):
    obj_user = User.query.filter_by(id=id).first()
    if not obj_user or not username or username == '' or not password1 or password1 == '' or password1 != password2:
        return False
    obj_user.username = username
    obj_user.password = password1
    db.session.commit()
    return True


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    obj_user = User.query.filter_by(username=request.form['username'], password=request.form['password']).first()
    if obj_user:
        flask_login.login_user(obj_user)
        return redirect(url_for('admin'))
    return redirect(url_for('login'))


@app.route('/logout')
def logout():
    flask_login.logout_user()
    return redirect(url_for('login'))


@login_manager.unauthorized_handler
def unauthorized_handler():
    return redirect(url_for('login'))


@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id=user_id).first()


@app.route('/admin', methods=['GET'])
@flask_login.login_required
def admin():
    vcards = VCard.query.filter(VCard.vc_property.startswith('FN')).order_by(VCard.vc_value).all()
    return render_template('contacts.html', vcards=vcards, user=flask_login.current_user,
                           show_avatars=bool_request_arg('avatars'), show_qrcodes=bool_request_arg('qrcodes'))


@app.route('/admin/user', methods=['GET', 'POST'])
@flask_login.login_required
def user():
    if request.method == 'POST':
        update_user(request.form['id'], request.form['username'], request.form['password1'], request.form['password2'])
    return render_template('user.html', user=flask_login.current_user)


@app.route('/admin/vcard/<uuid(strict=False):uid>', methods=['GET'])
@flask_login.login_required
def edit_card(uid):
    vcard_items = VCard.query.filter_by(uid=str(uid)).all()
    if not vcard_items:
        abort(404)
    return render_template('vcard.html', uid=str(uid), vcard_items=vcard_items, user=flask_login.current_user)


@app.route('/admin/upload', methods=['GET', 'POST'])
@flask_login.login_required
def get_avatar_upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.root_path, 'avatars', filename))
            return redirect(url_for('uploaded_file', filename=filename))
    return render_template('upload.html')


@app.route('/favicon.ico')
def favicon():
    abort(404)


@app.route('/')
@app.route('/index')
def index():
    return redirect(url_for('admin', qrcodes=1))


@app.route('/<string:uid>', methods=['GET'])
def get_card_short(uid):
    return get_card(suuid_decode(uid))


@app.route('/api/v1.0/sync/<uuid(strict=False):uid>', methods=['PUT'])
@require_appkey
def sync_vcard(uid):
    if not request.json:
        abort(400)
    (u, i) = ldap_sync(str(uid), request.json)
    # print(request.json)
    return jsonify({str(uid): {'updated': u, 'new': i}})


@app.route('/api/v1.0/vcards/<uuid(strict=False):uid>', methods=['GET'])
def get_card(uid):
    vcard_items = VCard.query.filter_by(uid=str(uid)).all()
    if not vcard_items:
        abort(404)
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
    if not VCard.query.filter_by(uid=str(uid)).first():
        abort(404)
    db.session.query(VCard).filter(VCard.uid == str(uid)).delete()
    db.session.commit()
    return jsonify({str(uid): 'DELETED'})


@app.route('/api/v1.0/vcards/all', methods=['DELETE'])
@require_appkey
def delete_all():
    db.session.query(VCard).delete()
    db.session.commit()
    return jsonify({'all': 'DELETED'})


# @app.route('/api/v1.0/contacts', methods=['GET'])
# @require_appkey
# def get_contacts():
#     vcards = VCard.query.filter(VCard.vc_property.startswith('FN')).order_by(VCard.vc_value).all()
#     if not vcards:
#         abort(404)
#     return render_template('contacts.html', vcards=vcards, show_images=True,
#                            show_avatars=bool_request_arg('avatars'), show_qrcodes=bool_request_arg('qrcodes'))


@app.route('/api/v1.0/avatars/<uuid(strict=False):uid>', methods=['GET'])
def get_avatar(uid):
    file_name = get_avatar_file_path(str(uid))
    if file_name:
        with open(file_name, 'rb') as bites:
            return send_file(io.BytesIO(bites.read()), attachment_filename=get_avatar_file_name(str(uid)),
                             mimetype=mimetypemap[app.config['AVATAR_FILE_TYPE']])
    abort(404)


@app.route('/api/v1.0/avatars/uploads/<filename>', methods=['GET'])
def uploaded_file(filename):
    return send_from_directory(os.path.join(app.root_path, 'avatars'), filename)


@app.route('/api/v1.0/qrcode/<uuid(strict=False):uid>', methods=['GET'])
def get_qrcode(uid):
    if not VCard.query.filter_by(uid=str(uid)).first():
        abort(404)
    return send_file(qrcode(url_for('get_card_short', uid=suuid_encode(uid), _external=True), mode='raw'),
                     mimetype='image/png')
