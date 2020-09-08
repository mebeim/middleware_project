import sys
from . import db
from os import urandom, makedirs, path
from flask import Flask

app  = Flask('rest-jpg')
home = path.expanduser('~')
test = '--test' in sys.argv

app.secret_key = urandom(64)
app.config.update({
	'schema'     : home + '/db/schema.sql',
	'database'   : '/tmp/db.sqlite' if test else (home + '/db/db.sqlite'),
	'upload_path': '/tmp/images' if test else (home + '/images')
})

makedirs(app.config['upload_path'], exist_ok=True)
db.init_app(app)

from . import routes

__all__ = ['app']
