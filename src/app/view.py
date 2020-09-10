from .constants import HTTP_401_UNAUTHORIZED
from flask import Response, request, render_template

def gen_template(filename, status=200, add_headers={}, **kwargs):
	data = render_template(filename + '.xml', **kwargs)
	headers = {'Cache-Control': 'no-cache, no-store, must-revalidate'}
	headers.update(add_headers)

	return Response(
		data,
		status=status,
		content_type='application/xml',
		headers=headers
	)


def success(message, status=200):
	return gen_template('success', status, message=message)


def success_redirect(message, redirect_path, status=303, this_host=True):
	headers = {'Location': (request.host_url if this_host else '') + redirect_path}
	return gen_template('success', status, headers, message=message)


def error(message, status):
	if status == HTTP_401_UNAUTHORIZED:
		headers = {'WWW-Authenticate': 'Basic realm="Middleware project", charset="UTF-8"'}
	else:
		headers = {}

	return gen_template('error', status, headers, code=status, message=message)


def user(u):
	return gen_template('user', id=u.id, name=u.name)


def users(all_users):
	def g():
		for u in all_users:
			yield u.id, u.name

	return gen_template('users', users=g())

def image(i):
	return gen_template('image', id=i.id, title=i.title, owner_id=i.owner_id)


def user_images(images):
	def g():
		for i in images:
			yield i.id, i.title, i.owner_id

	return gen_template('images', images=g())


def client(c):
	return gen_template('client', name=c.name, id=c.id, redirect_uri=c.redirect_uri)


def client_with_secret(c):
	return gen_template('client', name=c.name, id=c.id, redirect_uri=c.redirect_uri, secret=c.secret)


def token(t):
	return gen_template('token', value=t.value, user_id=t.user_id, client_id=t.client_id, scopes=' '.join(t.scopes))


def user_tokens(tokens):
	def g():
		for t in tokens:
			yield t.value, t.user_id, t.client_id, t.scopes

	return gen_template('tokens', tokens=g())
