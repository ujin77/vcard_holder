from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_uuid import FlaskUUID
from flask_qrcode import QRcode


app = Flask(__name__)
FlaskUUID(app)
qrcode = QRcode(app)


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vcholder.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['API_KEY'] = '1234567890'

db = SQLAlchemy(app)

import vcholder_app.routes
import vcholder_app.models

# db.drop_all()
db.create_all()

print(app.root_path)
