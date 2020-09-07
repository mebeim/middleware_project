from . import app, db, view, auth
from .utils import validate_user_id, validate_user_name
from .constants import *
from flask import Response, request, abort, send_file, g

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

	details = db.register_user(user_id, user_name, user_pw)
	if not details:
		return view.error('User ID already registered.', HTTP_403_FORBIDDEN)

	return view.success('Registration successful.', HTTP_200_OK)


@app.route('/users', methods=('GET',))
@auth.auth_required()
def users():
	return view.users(db.get_all_users())


@app.route('/user/<id>', methods=('GET',))
@auth.auth_required()
def user(**urlparams):
	user_id   = urlparams['id']
	user_name = db.get_user_name(user_id)

	if user_name is None:
		abort(HTTP_404_NOT_FOUND)

	return view.user(user_id, user_name)


@app.route('/user/<id>', methods=('DELETE',))
@auth.auth_required(oauth=False)
def user_delete(**urlparams):
	user_id = urlparams['id']

	if user_id != g.user_id:
		return view.error('Cannot delete a user different from yourself.', HTTP_403_FORBIDDEN)

	db.delete_user(user_id)
	return view.success('User successfully deleted.')


@app.route('/user/images'     , methods=('GET',), defaults={'id': None})
@app.route('/user/<id>/images', methods=('GET',))
@auth.auth_required()
def user_images(**urlparams):
	user_id = urlparams['id'] if urlparams['id'] is not None else g.user_id
	return view.user_images(user_id, db.get_all_user_images(user_id))


@app.route('/upload', methods=('POST',))
@auth.auth_required()
def image_upload():
	if not auth.can_write():
		return view.error('You do not have the appropriate scopes to perform this action.', HTTP_403_FORBIDDEN)

	user_id     = g.user_id
	image_file  = request.files.get('file')
	image_title = request.form.get('title', '').strip()

	if image_file is None or not image_title:
		return view.error('Missing parameters.', HTTP_400_BAD_REQUEST)

	image_id = db.save_image(image_file, image_title, user_id)
	if not image_id:
		return view.error('Unsupported file type, only JPEG allowed.', HTTP_400_BAD_REQUEST)

	return view.upload_success(image_id, image_title, user_id)


@app.route('/image/<int:id>', methods=('GET', 'DELETE'))
@auth.auth_required()
def image(**urlparams):
	image_id = urlparams['id']

	details = db.get_image_details(image_id)
	if not details:
		abort(HTTP_404_NOT_FOUND)

	image_title, image_owner = details

	if request.method == 'GET':
		return view.image(image_id, image_title, image_owner)
	elif request.method == 'DELETE':
		if not auth.can_write():
			return view.error('You do not have the appropriate scopes to perform this action.', HTTP_403_FORBIDDEN)

		if image_owner != g.user_id:
			return view.error("Cannot delete images of other users.", HTTP_403_FORBIDDEN)

		db.delete_image(image_id)
		return view.success('Image successfully deleted.')


@app.route('/image/<int:id>/download', methods=('GET',))
@auth.auth_required()
def image_download(**urlparams):
	image_id = urlparams['id']

	image_path = db.get_image_path(image_id)
	if image_path is None:
		abort(HTTP_404_NOT_FOUND)

	return send_file(image_path)


@app.route('/oauth/token', methods=('GET',))
@auth.auth_required(oauth=False)
def oauth_gen_token():
	scopes = request.args.get('scopes', '')
	if not scopes:
		return view.error('Missing required request parameter: scopes.', HTTP_400_BAD_REQUEST)

	token = auth.gen_token(g.user_id, scopes)
	if token is None:
		return view.error('Invalid token scopes.', HTTP_400_BAD_REQUEST)

	return view.token(token, g.user_id, scopes)


@app.route('/oauth/tokens', methods=('GET',))
@auth.auth_required(oauth=False)
def oauth_list_tokens():
	return view.user_tokens(g.user_id, db.get_all_user_tokens(g.user_id))


@app.route('/oauth/token/<tok>', methods=('GET',))
@auth.auth_required()
def oauth_get_token(**urlparams):
	token = urlparams['tok']
	if not token:
		abort(HTTP_404_NOT_FOUND)

	details = db.get_oauth_token_details(token)
	if details is None:
		abort(HTTP_404_NOT_FOUND)

	return view.token(*details)


@app.route('/oauth/token/<tok>', methods=('DELETE',))
@auth.auth_required(oauth=False)
def oauth_revoke_token(**urlparams):
	token = urlparams['tok'].strip()
	if not token:
		abort(HTTP_404_NOT_FOUND)

	tok = db.get_oauth_token_details(token)
	if tok is None:
		abort(HTTP_404_NOT_FOUND)

	db.delete_oauth_token(token)
	return view.success('OAuth token successfully revoked.')
