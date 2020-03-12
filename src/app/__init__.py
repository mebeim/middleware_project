from . import db
from os import urandom, makedirs
from flask import Flask

app = Flask('rest-jpg')

app.secret_key = urandom(64)
app.config.update({
	'database'   : 'db/database.sqlite',
	'upload_path': '/tmp/images'
})

makedirs(app.config['upload_path'], exist_ok=True)
db.init_app(app)

from . import routes

__all__ = ['app']
