from . import db, view
from .constants import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED
from os import urandom
from base64 import b64decode
from functools import wraps
from flask import request, g

OAUTH_SCOPES = {'read', 'write'}

def gen_token(user_id, scopes):
	sc = scopes.split()
	if not sc or any(s not in OAUTH_SCOPES for s in sc):
		return None

	token = urandom(64).hex()
	row = db.save_oauth_token(user_id, token, scopes)

	while row is None:
		token = urandom(64).hex()
		row = db.save_oauth_token(user_id, token, scopes)

	return token


def auth_required(basic=True, oauth=True):
	def decorator(f):
		@wraps(f)
		def authenticate(*args, **kwargs):
			auth = request.headers.get('Authorization', '').strip()

			try:
				kind, token = auth.split(' ')
				kind = kind.lower()
			except:
				return view.error('Invalid or missing credentials.', HTTP_401_UNAUTHORIZED)

			if kind == 'basic':
				if not basic:
					return view.error('Invalid credential type for this endpoint.', HTTP_400_BAD_REQUEST)

				try:
					user_id, user_pw = b64decode(token).decode().split(':')
				except:
					return view.error('Malformed credentials.', HTTP_400_BAD_REQUEST)

				details = db.login_user(user_id, user_pw)
				if not details:
					return view.error('Invalid credentials.', HTTP_401_UNAUTHORIZED)

				g.user_id, g.user_name = details
				g.auth_type = 'basic'

			elif kind == 'bearer':
				if not oauth:
					return view.error('Invalid credential type for this endpoint.', HTTP_400_BAD_REQUEST)

				details = db.oauth_user(token)
				if details is None:
					return view.error('Invalid token.', HTTP_401_UNAUTHORIZED)

				g.user_id, g.user_name, g.oauth_scopes = details
				g.oauth_scopes = set(g.oauth_scopes.split(' '))
				g.auth_type = 'oauth'

			else:
				return view.error('Invalid authorization type.', HTTP_400_BAD_REQUEST)

			return f(*args, **kwargs)

		return authenticate

	return decorator


def can_write():
	return g.auth_type == 'basic' or (g.auth_type == 'oauth' and 'write' in g.oauth_scopes)
