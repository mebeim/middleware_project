import os
import sys
import sqlite3
from .utils import validate_jpeg_file
from hashlib import sha512
from shutil import rmtree
from datetime import datetime
from flask import current_app, g

def get_db():
	if 'db' not in g:
		db_path = current_app.config['database']
		init = '--reset-db' in sys.argv or not os.path.isfile(db_path)
		g.db = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
		g.db.row_factory = sqlite3.Row

		if init:
			schema_path = current_app.config['schema']

			with current_app.open_resource(schema_path) as f:
				g.db.executescript(f.read().decode())

	return g.db


def close_db(e=None):
	db = g.pop('db', None)
	if db is not None:
		db.close()


def get_cursor():
	return get_db().cursor()


def query_one(query, parameters):
	c = get_cursor()

	if parameters:
		c.execute(query, parameters)
	else:
		c.execute(query)

	return c.fetchone()


def query_all(query, parameters):
	c = get_cursor()

	if parameters:
		c.execute(query, parameters)
	else:
		c.execute(query)

	row = c.fetchone()
	while row is not None:
		yield row
		row = c.fetchone()


def write_and_commit(*queries_parameters):
	c = get_cursor()

	for query, parameters in queries_parameters:
		if parameters:
			c.execute(query, parameters)
		else:
			c.execute(query)

	c.connection.commit()
	return c.lastrowid


def init_app(app):
	app.teardown_appcontext(close_db)
