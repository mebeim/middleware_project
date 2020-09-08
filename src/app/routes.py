from . import app, view, auth
from .model import *
from .constants import *
from .utils import validate_user_id, validate_user_name, validate_jpeg_file
from flask import request, abort, send_file, g

@app.errorhandler(HTTP_400_BAD_REQUEST)
@app.errorhandler(HTTP_404_NOT_FOUND)
@app.errorhandler(HTTP_405_METHOD_NOT_ALLOWED)
@app.errorhandler(HTTP_500_SERVER_ERROR)
def error_handler(error):
	code = error.code
	msg = '{}{}'.format(
		error.name if error.name else 'Error {}'.format(code),
		(': ' + error.description) if error.description else ''
	)

	return view.error(msg, code)


@app.route('/register', methods=('POST',))
def register():
	user_id   = request.form.get('id')
	user_name = request.form.get('name', '').strip()
	user_pw   = request.form.get('password')

	if not user_id or not user_name or not user_pw:
		return view.error('Missing parameters.', HTTP_400_BAD_REQUEST)

	if not validate_user_id(user_id):
		return view.error('Invalid user ID.', HTTP_400_BAD_REQUEST)

	if not validate_user_name(user_name):
		return view.error('Invalid name.', HTTP_400_BAD_REQUEST)

	user = User.register(user_id, user_name, user_pw)
	if not user:
		return view.error('User ID already registered.', HTTP_403_FORBIDDEN)

	return view.success('Registration successful.', HTTP_200_OK)


@app.route('/users', methods=('GET',))
@auth.auth_required(allow_oauth=False)
def users():
	return view.users(User.get_all())


@app.route('/user/<id>', methods=('GET',))
@auth.auth_required()
def user(**urlparams):
	user_id = urlparams['id']
	if g.auth_type == 'oauth' and g.user.id != user_id:
		return view.error('Cannot access other users.', HTTP_403_FORBIDDEN)

	user = User.get(user_id)
	if user is None:
		abort(HTTP_404_NOT_FOUND)

	return view.user(user)


@app.route('/user/<id>', methods=('DELETE',))
@auth.auth_required(allow_oauth=False)
def user_delete(**urlparams):
	if urlparams['id'] != g.user.id:
		return view.error('Cannot delete a user different from yourself.', HTTP_403_FORBIDDEN)

	g.user.delete()
	return view.success('User successfully deleted.')


@app.route('/user/<id>/images', methods=('GET',))
@auth.auth_required()
def user_images(**urlparams):
	user_id = urlparams['id']
	if g.auth_type == 'oauth' and g.user.id != user_id:
		return view.error('Cannot access images owned by other users.', HTTP_403_FORBIDDEN)

	user = User.get(user_id)
	if user is None:
		abort(HTTP_404_NOT_FOUND)

	return view.user_images(user.images)


@app.route('/upload', methods=('POST',))
@auth.auth_required(allow_oauth='write')
def image_upload():
	image_file  = request.files.get('file')
	if image_file is None:
		return view.error('Missing required request parameter: file.', HTTP_400_BAD_REQUEST)

	image_title = request.form.get('title', '').strip()
	if not image_title:
		return view.error('Missing required request parameter: title.', HTTP_400_BAD_REQUEST)

	if not validate_jpeg_file(image_file):
		return view.error('Unsupported file type, only JPEG allowed.', HTTP_400_BAD_REQUEST)

	image = Image.upload(image_title, g.user.id, image_file)
	return view.success_redirect('Image successfully uploaded.', 'image/{}'.format(image.id))


@app.route('/image/<int:id>', methods=('GET',))
@auth.auth_required()
def image_get(**urlparams):
	image_id = urlparams['id']

	image = Image.get(image_id)
	if image is None:
		abort(HTTP_404_NOT_FOUND)

	if g.auth_type == 'oauth' and image.owner_id != g.user.id:
		return view.error('Cannot access images owned by other users.', HTTP_403_FORBIDDEN)

	return view.image(image)


@app.route('/image/<int:id>', methods=('DELETE',))
@auth.auth_required(allow_oauth='write')
def image_delete(**urlparams):
	image = Image.get(urlparams['id'])
	if image is None:
		abort(HTTP_404_NOT_FOUND)

	if image.owner_id != g.user.id:
		return view.error("Cannot delete images owned by other users.", HTTP_403_FORBIDDEN)

	image.delete()
	return view.success('Image successfully deleted.')


@app.route('/image/<int:id>/download', methods=('GET',))
@auth.auth_required()
def image_download(**urlparams):
	image = Image.get(urlparams['id'])
	if image is None:
		abort(HTTP_404_NOT_FOUND)

	if g.auth_type == 'oauth' and image.owner_id != g.user.id:
		return view.error('Cannot access images owned by other users.', HTTP_403_FORBIDDEN)

	return send_file(image.path)


@app.route('/oauth/register-client', methods=('POST',))
def oauth_register_client():
	client_name = request.form.get('name', '').strip()
	if not client_name:
		return view.error('Missing required request parameter: name.', HTTP_400_BAD_REQUEST)

	redirect_uri = request.form.get('redirect_uri', '').strip()
	if not redirect_uri:
		return view.error('Missing required request parameter: redirect_uri.', HTTP_400_BAD_REQUEST)

	if not validate_user_name(client_name):
		return view.error('Invalid name.', HTTP_400_BAD_REQUEST)

	client = Client.register(client_name, redirect_uri)
	return view.client_with_secret(client)


@app.route('/oauth/authorize', methods=('GET',))
@auth.auth_required(allow_oauth=False)
def oauth_authorize():
	keys = ('response_type', 'client_id', 'redirect_uri', 'scopes')

	for k in keys:
		if k not in request.args:
			return view.error(f'Missing required request parameter: {k}.', HTTP_400_BAD_REQUEST)

	response_type = request.args['response_type']
	if response_type != 'token':
		return view.error('Unsupported response_type.', HTTP_400_BAD_REQUEST)

	response_mode = request.args.get('response_mode', 'fragment')
	if response_mode != 'fragment':
		return view.error('Unsupported response_mode.', HTTP_400_BAD_REQUEST)

	client = Client.get(request.args['client_id'])
	if client == None:
		return view.error('Invalid client_id.', HTTP_400_BAD_REQUEST)

	redirect_uri = request.args['redirect_uri']
	if redirect_uri != client.redirect_uri:
		return view.error('Invalid redirect_uri.', HTTP_400_BAD_REQUEST)

	scopes = request.args['scopes']
	token = Token.generate(g.user.id, client.id, scopes)
	if token is None:
		return view.error('Invalid scopes.', HTTP_400_BAD_REQUEST)

	redirect_uri = f'{redirect_uri}?token={token.value}'
	return view.success_redirect('Client successfully authorized.', redirect_uri, status=302, this_host=False)


@app.route('/oauth/tokens', methods=('GET',))
@auth.auth_required(allow_oauth=False)
def oauth_list_tokens():
	return view.user_tokens(g.user.tokens)


@app.route('/oauth/token/<tok>', methods=('GET',))
@auth.auth_required()
def oauth_get_token(**urlparams):
	token = Token.get(urlparams['tok'])
	if token is None:
		abort(HTTP_404_NOT_FOUND)

	return view.token(token)


@app.route('/oauth/token/<tok>', methods=('DELETE',))
@auth.auth_required(allow_oauth=False)
def oauth_revoke_token(**urlparams):
	token = Token.get(urlparams['tok'])
	if token is None:
		abort(HTTP_404_NOT_FOUND)

	token.delete()
	return view.success('OAuth token successfully revoked.')


@app.route('/oauth/client/<id>', methods=('GET',))
@auth.auth_required()
def oauth_get_client(**urlparams):
	client = Client.get(urlparams['id'])
	if client is None:
		abort(HTTP_404_NOT_FOUND)

	return view.client(client)
