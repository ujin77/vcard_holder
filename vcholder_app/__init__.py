import os
import uuid
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_uuid import FlaskUUID
from flask_qrcode import QRcode
from flask_login import LoginManager
from logging.handlers import RotatingFileHandler
from logging import Formatter
import logging

VCARD_SERVER_CONFIG = '%s.cfg' % __name__

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vcholder.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = uuid.uuid4().hex
app.config['AVATAR_FILE_TYPE'] = 'jpeg'
app.config['DEFAULT_UUID'] = '00000000-0000-0000-0000-000000000000'
app.config['LOGFILE'] = '%s.log' % __name__
app.config['DEBUG_CONFIG'] = "FALSE"

app.config.from_pyfile(os.getenv('VCARD_SERVER_CONFIG', VCARD_SERVER_CONFIG), True)

FlaskUUID(app)
qr = QRcode(app)
lm = LoginManager(app)
db = SQLAlchemy(app)

handler = RotatingFileHandler(app.config['LOGFILE'], maxBytes=1000000, backupCount=3)
handler.setFormatter(Formatter('%(asctime)s %(levelname)s: %(message)s'))
if app.config['DEBUG']:
    handler.setFormatter(Formatter('%(asctime)s %(levelname)s [%(module)s.%(funcName)s]: %(message)s'))
elif 'LOGLEVEL' in app.config:
    app.logger.setLevel(logging.getLevelName(app.config['LOGLEVEL']))
app.logger.addHandler(handler)

if app.config['DEBUG'] and app.config['DEBUG_CONFIG'] == 'TRUE':
    for c in app.config:
        app.logger.debug("%s: %s" % (c, app.config[c]))

import vcholder_app.routes
import vcholder_app.models

vcholder_app.models.on_init_db()


