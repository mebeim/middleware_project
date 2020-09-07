from . import db
from os import urandom, makedirs, path
from flask import Flask

app = Flask('rest-jpg')

app.secret_key = urandom(64)
app.config.update({
	'database'   : 'db/database.sqlite',
	'schema'     : 'db/schema.sql',
	'upload_path': path.expanduser('~') + '/images'
})

makedirs(app.config['upload_path'], exist_ok=True)
db.init_app(app)

from . import routes

__all__ = ['app']
