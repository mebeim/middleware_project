import re
from . import view
from .constants import HTTP_400_BAD_REQUEST
from struct import unpack
from functools import wraps
from flask import request

USER_ID_REGEXP   = re.compile(r'^[a-zA-Z0-9_-]{1,255}$')
USER_NAME_REGEXP = re.compile(r'^[ a-zA-Z0-9_.-]{1,255}$')

def validate_user_id(user_id):
	return USER_ID_REGEXP.match(user_id) is not None

def validate_user_name(user_name):
	return USER_NAME_REGEXP.match(user_name) is not None

def validate_jpeg_file(file):
	magic = unpack('>L', file.read(4))[0]

	if magic in (0xFFD8FFDB, 0xFFD8FFEE):
		res = True
	elif magic == 0xFFD8FFE0:
		res = unpack('>LL', file.read(8)) == (0x00104A46, 0x49460001)
	elif magic == 0xFFD8FFE1:
		res = unpack('>HHL', file.read(8))[1:] == (0x4578, 0x69660000)
	else:
		res = False

	file.seek(0)

	return res

def need_params(*needed):
	def decorator(f):
		@wraps(f)
		def check_params(*args, **kwargs):
			params = request.args if request.method == 'GET' else request.form

			for k in needed:
				if not params.get(k, ''):
					return view.error(f'Missing required request parameter: {k}.', HTTP_400_BAD_REQUEST)

			return f(*args, **kwargs)

		return check_params

	return decorator
