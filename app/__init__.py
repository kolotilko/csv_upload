import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

flask_app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'files')
SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:master@localhost/test'
SQLALCHEMY_MIGRATE_REPO = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'migrations')

flask_app.config['SECRET_KEY'] = 'top-secret!'
flask_app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
flask_app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
flask_app.config['SQLALCHEMY_MIGRATE_REPO'] = SQLALCHEMY_MIGRATE_REPO
db = SQLAlchemy(flask_app)

from app import views
from app import models
