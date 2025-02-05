from . import view
from .model import *
from .constants import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN
from base64 import b64decode
from functools import wraps
from flask import request, g

OAUTH_SCOPES = {'read', 'write'}

def check_scopes(scopes):
	sc = set(scopes.strip().split())

	if sc and all(s in OAUTH_SCOPES for s in sc):
		sc.add('read')
		return ' '.join(sc)
	else:
		return None


def auth_required(allow_user=True, allow_oauth='read', allow_client=False):
	def decorator(f):
		@wraps(f)
		def authenticate(*args, **kwargs):
			auth = request.headers.get('Authorization', '').strip()

			try:
				kind, payload = auth.split(' ')
				kind = kind.lower()
			except:
				return view.error('Invalid or missing credentials.', HTTP_401_UNAUTHORIZED)

			if kind == 'basic':
				try:
					auth_id, auth_pw = b64decode(payload).decode().split(':')
				except:
					return view.error('Malformed credentials.', HTTP_400_BAD_REQUEST)

				client = None
				user   = None

				if auth_id.startswith('$'):
					if not allow_client:
						return view.error('Invalid credential type for this endpoint.', HTTP_400_BAD_REQUEST)

					client = Client.login(auth_id, auth_pw)
				else:
					if not allow_user:
						return view.error('Invalid credential type for this endpoint.', HTTP_400_BAD_REQUEST)

					user = User.login(auth_id, auth_pw)

				if user is None and client is None:
					return view.error('Invalid credentials.', HTTP_401_UNAUTHORIZED)

				g.user   = user
				g.client = client
				g.oauth  = False

			elif kind == 'bearer':
				if not allow_oauth:
					return view.error('Invalid credential type for this endpoint.', HTTP_400_BAD_REQUEST)

				token = Token.get(payload)
				if token is None:
					return view.error('Invalid token.', HTTP_401_UNAUTHORIZED)

				if allow_oauth != '*' and allow_oauth not in token.scopes:
					return view.error('Token has insufficient authorization scopes.', HTTP_403_FORBIDDEN)

				g.token = token
				g.user  = token.user
				g.oauth = True

			else:
				return view.error('Invalid authorization type.', HTTP_400_BAD_REQUEST)

			return f(*args, **kwargs)

		return authenticate

	return decorator
