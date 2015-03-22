from flask import Flask

from flask.ext.socketio import SocketIO

app = Flask(__name__)

app.config.from_object('secret_config')

app.socketio = SocketIO(app)

from app import views
from app import api
from app import config
from app import chat
