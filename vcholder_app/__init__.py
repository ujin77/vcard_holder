from flask import Flask
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vcholder.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['API_KEY'] = '1234567890'

db = SQLAlchemy(app)

import vcholder_app.routes
import vcholder_app.models

# db.drop_all()
db.create_all()


