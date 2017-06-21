import logging
from logging import StreamHandler
from flask import Flask, Blueprint
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from config import config

db = SQLAlchemy()
blueprint = Blueprint('app_views', __name__)
corss = CORS()


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    db.init_app(app)

    app.register_blueprint(blueprint)

    if not app.testing and not app.config.get('SSL_DISABLE'):
        from flask_sslify import SSLify
        sslify = SSLify(app)

    corss.init_app(app)

    # log to stderr
    file_handler = StreamHandler()
    app.logger.addHandler(file_handler)
    if config_name == 'production':
        app.logger.setLevel(logging.INFO)  # TODO: later only log at warning level
    else:
        app.logger.setLevel(logging.INFO)

    return app

from . import views
