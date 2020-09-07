import os
from . import db, auth
from contextlib import suppress
from sqlite3 import IntegrityError
from hashlib import sha512
from flask import current_app

__all__ = ['User', 'Image', 'Token']

class User:
	def __init__(self, idd, name):
		self.id   = idd
		self.name = name

	@property
	def images(self):
		for row in db.query_all('SELECT * FROM images WHERE owner_id=?', (self.id,)):
			yield Image(*row)

	@property
	def tokens(self):
		for row in db.query_all('SELECT * FROM oauth_tokens WHERE user_id=?', (self.id,)):
			yield Token(*row)

	@staticmethod
	def get(idd):
		row = db.query_one('SELECT id, name FROM users WHERE id=?', (idd,))
		if row is None:
			return None

		return User(*row)

	@staticmethod
	def get_all(idd):
		for row in db.query_all('SELECT id, name FROM users ORDER BY id'):
			yield User(*row)

	@staticmethod
	def register(idd, name, password):
		pw_hash = sha512(password.encode()).hexdigest()

		try:
			db.write_and_commit(('INSERT INTO users VALUES (?, ?, ?)', (idd, name, pw_hash)))
		except IntegrityError:
			return None

		return User(idd, name)

	@staticmethod
	def login(idd, password):
		pw_hash = sha512(password.encode()).hexdigest()

		row = db.query_one('SELECT id, name FROM users WHERE id=? AND password_hash=?', (idd, pw_hash))
		if row is None:
			return None

		return User(*row)

	def delete(self):
		db.write_and_commit(
			('DELETE FROM users WHERE id=?', (user_id,)),
			('DELETE FROM images WHERE owner_id=?', (user_id,)),
			('DELETE FROM oauth_tokens WHERE user_id=?', (user_id,))
		)

		user_dir = os.path.join(current_app.config['upload_path'], user_id)
		rmtree(user_dir, ignore_errors=True)


class Image:
	def __init__(self, idd, title, owner_id):
		self.id       = idd
		self.title    = title
		self.owner_id = owner_id
		self.path     = os.path.join(current_app.config['upload_path'], self.owner_id, '{:d}.jpg'.format(self.id))

	@staticmethod
	def get(idd):
		row = db.query_one('SELECT * FROM images WHERE id=?', (idd,))
		if row is None:
			return None

		return Image(*row)

	@staticmethod
	def upload(title, owner_id, file):
		idd = db.write_and_commit(('INSERT INTO images (title, owner_id) VALUES (?, ?)', (title, owner_id)))
		path = os.path.join(current_app.config['upload_path'], owner_id, '{:d}.jpg'.format(idd))

		with suppress(FileNotFoundError):
			os.remove(path)

		user_dir = os.path.join(current_app.config['upload_path'], owner_id)
		os.makedirs(user_dir, exist_ok=True)
		file.save(path)

		return Image(idd, title, owner_id)

	def delete(self):
		db.write_and_commit(('DELETE FROM images WHERE id=?', (self.id,)))

		with suppress(FileNotFoundError):
			os.remove(self.path)


class Token:
	def __init__(self, value, user_id, scopes):
		self.value   = value
		self.user_id = user_id
		self.scopes  = set(scopes.split())
		self._user   = None

	@property
	def user(self):
		if self._user is None:
			row = db.query_one('SELECT id, name FROM users WHERE id=?', (self.user_id,))
			self._user = User(*row)

		return self._user

	@staticmethod
	def get(value):
		row = db.query_one('SELECT token, user_id, scopes FROM oauth_tokens WHERE token=?', (value,))
		if row is None:
			return None

		return Token(*row)

	@staticmethod
	def generate(user_id, scopes):
		if not auth.check_scopes(scopes):
			return None

		while 1:
			value = os.urandom(64).hex()

			try:
				db.write_and_commit(('INSERT INTO oauth_tokens (token, user_id, scopes) VALUES (?, ?, ?)', (value, user_id, scopes)))
				break
			except IntegrityError:
				continue

		return Token(value, user_id, scopes)

	def delete(self):
		db.write_and_commit(('DELETE FROM oauth_tokens WHERE token=?', (self.value,)))
