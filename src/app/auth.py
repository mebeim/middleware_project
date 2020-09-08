from . import view
from .model import *
from .constants import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN
from base64 import b64decode
from functools import wraps
from flask import request, g

OAUTH_SCOPES = {'read', 'write'}

def check_scopes(scopes):
	sc = set(scopes.strip().split())
	return sc and all(s in OAUTH_SCOPES for s in sc)


def auth_required(allow_user=True, allow_oauth='read', owner_only=False):
	def decorator(f):
		@wraps(f)
		def authenticate(*args, **kwargs):
			auth = request.headers.get('Authorization', '').strip()

			try:
				kind, payload = auth.split(' ')
				kind = kind.lower()
			except:
				return view.error('Invalid or missing credentials.', HTTP_401_UNAUTHORIZED)

			if kind != 'basic':
				return view.error('Invalid authorization type.', HTTP_400_BAD_REQUEST)

			try:
				auth_id, auth_pw = b64decode(payload).decode().split(':')
			except:
				return view.error('Malformed credentials.', HTTP_400_BAD_REQUEST)

			if auth_id.startswith('$'):
				if not allow_oauth:
					return view.error('Invalid credential type for this endpoint.', HTTP_400_BAD_REQUEST)

				client = Client.login(auth_id, auth_pw)
				if client is None:
					return view.error('Invalid credentials.', HTTP_401_UNAUTHORIZED)

				token = request.args.get('token')
				if token is None:
					return view.error('Invalid token.', HTTP_401_UNAUTHORIZED)

				token = Token.get(token)
				if token is None:
					return view.error('Invalid token.', HTTP_401_UNAUTHORIZED)

				if allow_oauth != '*' and allow_oauth not in token.scopes:
					return view.error('Token has insufficient authorization scopes.', HTTP_403_FORBIDDEN)

				g.token = token
				g.user = token.user
				g.auth_type = 'oauth'

			else:
				if not allow_user:
					return view.error('Invalid credential type for this endpoint.', HTTP_400_BAD_REQUEST)

				user = User.login(auth_id, auth_pw)
				if user is None:
					return view.error('Invalid credentials.', HTTP_401_UNAUTHORIZED)

				g.user = user
				g.auth_type = 'basic'

			return f(*args, **kwargs)

		return authenticate

	return decorator


def can_write():
	return g.auth_type == 'basic' or (g.auth_type == 'oauth' and 'write' in g.oauth_scopes)
