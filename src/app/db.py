import os
import sqlite3
import click
from .utils import validate_jpeg_file
from hashlib import sha512
from shutil import rmtree
from datetime import datetime
from flask import current_app, g
from flask.cli import with_appcontext

def get_db():
	if 'db' not in g:
		g.db = sqlite3.connect(
			current_app.config['database'],
			detect_types=sqlite3.PARSE_DECLTYPES
		)

		g.db.row_factory = sqlite3.Row

	return g.db


def close_db(e=None):
	db = g.pop('db', None)

	if db is not None:
		db.close()


def init_db():
	db = get_db()

	with current_app.open_resource('db/schema.sql') as f:
		db.executescript(f.read().decode())


@click.command('init-db')
@with_appcontext
def init_db_command():
	init_db()
	click.echo('Database initialized.')


def init_app(app):
	app.teardown_appcontext(close_db)
	app.cli.add_command(init_db_command)


################################################################################


def login_user(user_id, user_pw):
	cursor = get_db().cursor()
	pw_hash = sha512(user_pw.encode()).hexdigest()

	values = (user_id, pw_hash)
	cursor.execute('SELECT id, name FROM users WHERE id=? AND password_hash=?', values)
	return cursor.fetchone()


def oauth_user(token):
	cursor = get_db().cursor()
	cursor.execute('SELECT user_id, scopes FROM oauth_tokens WHERE token=?', (token,))

	row = cursor.fetchone()
	if row is None:
		return None

	user_id, scopes = row
	cursor.execute('SELECT name FROM users WHERE id=?', (user_id,))

	row = cursor.fetchone()
	if row is None:
		return None

	user_name = row[0]
	return user_id, user_name, scopes


def save_oauth_token(user_id, token, scopes):
	cursor = get_db().cursor()

	try:
		cursor.execute('INSERT INTO oauth_tokens (token, user_id, scopes) VALUES (?, ?, ?)', (token, user_id, scopes))
		cursor.connection.commit()
	except sqlite3.IntegrityError:
		return None

	return token


def get_oauth_token_details(token):
	cursor = get_db().cursor()
	cursor.execute('SELECT token, user_id, scopes FROM oauth_tokens WHERE token=?', (token,))
	return cursor.fetchone()


def delete_oauth_token(token):
	cursor = get_db().cursor()
	cursor.execute('DELETE FROM oauth_tokens WHERE token=?', (token,))
	cursor.connection.commit()


def register_user(user_id, user_name, user_pw):
	cursor = get_db().cursor()
	pw_hash = sha512(user_pw.encode()).hexdigest()

	values = (user_id, user_name, pw_hash)

	try:
		cursor.execute('INSERT INTO users VALUES (?, ?, ?)', values)
		cursor.connection.commit()
	except sqlite3.IntegrityError:
		return None

	return user_id, user_name


def get_user_name(user_id):
	cursor = get_db().cursor()
	cursor.execute('SELECT name FROM users WHERE id=?', (user_id,))

	row = cursor.fetchone()
	if row is None:
		return None

	return row[0]


def delete_user(user_id):
	cursor = get_db().cursor()

	cursor.execute('DELETE FROM users WHERE id=?', (user_id,))
	cursor.execute('DELETE FROM images WHERE owner=?', (user_id,))
	cursor.execute('DELETE FROM oauth_tokens WHERE user_id=?', (user_id,))
	cursor.connection.commit()

	base_path = current_app.config['upload_path']
	imgs_path = os.path.join(base_path, user_id)
	rmtree(imgs_path, ignore_errors=True)


def get_all_users():
	cursor = get_db().cursor()
	cursor.execute('SELECT id, name FROM users ORDER BY id')

	row = cursor.fetchone()
	while row is not None:
		yield row
		row = cursor.fetchone()


def save_image(image_file, image_title, image_owner):
	try:
		ok = validate_jpeg_file(image_file)
	except:
		ok = False

	if not ok:
		return None

	cursor = get_db().cursor()
	values = (image_title, image_owner)
	cursor.execute('INSERT INTO images (title, owner) VALUES (?, ?)', values)
	cursor.connection.commit()

	image_id  = cursor.lastrowid
	base_path = current_app.config['upload_path']
	file_name = '{:d}.jpg'.format(image_id)
	file_path = os.path.join(base_path, image_owner, file_name)

	try:
		os.remove(file_path)
	except:
		pass

	os.makedirs(os.path.join(base_path, image_owner), exist_ok=True)
	image_file.save(file_path)

	return image_id


def get_image_details(image_id):
	cursor = get_db().cursor()
	cursor.execute('SELECT title, owner FROM images WHERE id=?', (image_id,))

	row = cursor.fetchone()
	return row


def get_image_path(image_id):
	cursor = get_db().cursor()
	cursor.execute('SELECT owner FROM images WHERE id=?', (image_id,))

	row = cursor.fetchone()
	if row is None:
		return None

	image_owner = row[0]
	base_path   = current_app.config['upload_path']
	file_name   = '{:d}.jpg'.format(image_id)

	return os.path.join(base_path, image_owner, file_name)


def delete_image(image_id):
	cursor = get_db().cursor()
	cursor.execute('DELETE FROM images WHERE id=?', (image_id,))
	cursor.connection.commit()
	img_path = get_image_path(image_id)
	rmtree(img_path, ignore_errors=True)


def get_all_user_images(user_id):
	cursor = get_db().cursor()
	cursor.execute('SELECT * FROM images WHERE owner=?', (user_id,))

	row = cursor.fetchone()
	while row is not None:
		yield row
		row = cursor.fetchone()


def get_all_user_tokens(user_id):
	cursor = get_db().cursor()
	cursor.execute('SELECT * FROM oauth_tokens WHERE user_id=?', (user_id,))

	row = cursor.fetchone()
	while row is not None:
		yield row
		row = cursor.fetchone()
