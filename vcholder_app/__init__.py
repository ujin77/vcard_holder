from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_uuid import FlaskUUID


app = Flask(__name__)
FlaskUUID(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vcholder.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['API_KEY'] = '1234567890'

db = SQLAlchemy(app)

import vcholder_app.routes
import vcholder_app.models

# db.drop_all()
db.create_all()
