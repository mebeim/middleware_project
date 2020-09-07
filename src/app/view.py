from .constants import HTTP_401_UNAUTHORIZED
from os import path
from flask import Response, request, session, render_template

def gen_template(filename, status=200, auth=False, **kwargs):
	data = render_template(filename + '.xml', **kwargs)
	headers = {'Cache-Control': 'no-cache, no-store, must-revalidate'}

	if auth:
		headers['WWW-Authenticate']  = 'Basic realm="middleware"\nBearer realm="middleware"'

	return Response(
		data,
		status=status,
		content_type='application/xml',
		headers=headers
	)

def success(message, status=200):
	return gen_template('success', status, **{'message': message})

def error(message, status):
	auth = status == HTTP_401_UNAUTHORIZED
	return gen_template('error', status, auth=auth, **{'code': status, 'message': message})

def user(user_id, user_name):
	return gen_template('user', **{'id': user_id, 'name': user_name})

def users(all_users):
	return gen_template('users', **{'users': all_users})

def image(image_id, image_title, owner_id):
	return gen_template('image', id=image_id, title=image_title, owner_id=owner_id)

def user_images(user_id, user_images):
	return gen_template('images', owner_id=user_id, images=user_images)

def upload_success(image_id, image_title, owner_id):
	return image(image_id, image_title, owner_id)

def token(token, user_id, scopes):
	return gen_template('token', **{'value': token, 'user_id': user_id, 'scopes': scopes})

def user_tokens(user_id, user_tokens):
	return gen_template('tokens', user_id=user_id, tokens=user_tokens)
