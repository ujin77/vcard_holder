from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_uuid import FlaskUUID
from flask_qrcode import QRcode
import os

VCH_CONFIG = '%s.cfg' % __name__

app = Flask(__name__)

FlaskUUID(app)
qrcode = QRcode(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vcholder.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['API_KEY'] = '1234567890'
app.config['SECRET_KEY'] = '1234567890'
app.config['AVATAR_FILE_TYPE'] = 'jpeg'
app.config['DEFAULT_UUID'] = '00000000-0000-0000-0000-000000000000'

app.config.from_pyfile(os.getenv('VCH_CONFIG', VCH_CONFIG), True)

db = SQLAlchemy(app)

import vcholder_app.routes
import vcholder_app.models

# db.drop_all()
db.create_all()
