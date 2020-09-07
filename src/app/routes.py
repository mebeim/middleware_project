from . import app, view, auth
from .model import *
from .constants import *
from .utils import validate_user_id, validate_user_name, validate_jpeg_file
from flask import request, abort, send_file, redirect, g

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


@app.route('/oauth/token', methods=('GET',))
@auth.auth_required(allow_oauth=False)
def oauth_gen_token():
	scopes = request.args.get('scopes', '')
	if not scopes:
		return view.error('Missing required request parameter: scopes.', HTTP_400_BAD_REQUEST)

	token = Token.generate(g.user.id, scopes)
	if token is None:
		return view.error('Invalid token scopes.', HTTP_400_BAD_REQUEST)

	return view.token(token)


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
