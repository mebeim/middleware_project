from . import app, db, view
from .utils import validate_user_id, validate_user_name
from .constants import *
from flask import Response, request, session, abort, send_file

@app.errorhandler(HTTP_400_BAD_REQUEST)
@app.errorhandler(HTTP_404_NOT_FOUND)
@app.errorhandler(HTTP_405_METHOD_NOT_ALLOWED)
@app.errorhandler(HTTP_500_SERVER_ERROR)
def error_handler(error):
	code = error.code
	msg = '{}{}'.format(
		error.name if error.name else 'Error {}'.format(code),
		(' - ' + error.description) if error.description else ''
	)

	return view.error(msg, code)


@app.route('/login', methods=('POST',))
def login():
	user_id = session.get('user_id')

	if user_id is not None:
		return view.error('Already logged in.', HTTP_403_FORBIDDEN)

	user_id = request.form.get('id')
	user_pw = request.form.get('password')

	if not user_id or not user_pw:
		return view.error('Missing parameters.', HTTP_400_BAD_REQUEST)

	details = db.login_user(user_id, user_pw)
	if not details:
		return view.error('Bad credentials.', HTTP_401_UNAUTHORIZED)

	session['user_id'], session['user_name'] = details

	return view.success('Login successful.')


@app.route('/logout', methods=('GET',))
def logout():
	user_id = session.pop('user_id', None)
	session.pop('user_name', None)

	if user_id is None:
		return view.error('Already logged out.', HTTP_403_FORBIDDEN)

	return view.success('Logout successful.')


@app.route('/register', methods=('POST',))
def register():
	user_id = session.get('user_id')

	if user_id is not None:
		return view.error('Already logged in, log out first.', HTTP_403_FORBIDDEN)

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

	session['user_id'], session['user_name'] = details

	return view.success('Registration successful.', HTTP_200_OK)


@app.route('/users', methods=('GET',))
def users():
	return view.users(db.get_all_users())


@app.route('/user'     , methods=('GET', 'DELETE'), defaults={'id': None})
@app.route('/user/<id>', methods=('GET', 'DELETE'))
def user(**urlparams):
	logged_user_id   = session.get('user_id')
	logged_user_name = session.get('user_name')

	if urlparams['id'] is not None:
		user_id = urlparams['id']

		if request.method == 'GET':
			user_name = db.get_user_details(user_id)
	else:
		if logged_user_id is None:
			return view.error('Login required.', HTTP_401_UNAUTHORIZED)

		user_id = logged_user_id

		if request.method == 'GET':
			user_name = logged_user_name

	if request.method == 'GET':
		if user_name is None:
			abort(HTTP_404_NOT_FOUND)

		return view.user(user_id, user_name)

	if user_id != logged_user_id:
		return view.error('Cannot delete a user different from the currently logged in user.', HTTP_401_UNAUTHORIZED)

	db.delete_user(user_id)
	session.pop('user_id', None)
	session.pop('user_name', None)

	return view.success('User successfully deleted. You are now logged out.')


@app.route('/user/images'     , methods=('GET',), defaults={'id': None})
@app.route('/user/<id>/images', methods=('GET',))
def user_images(**urlparams):
	logged_user_id = session.get('user_id')

	if urlparams['id'] is not None:
		user_id = urlparams['id']
	else:
		if logged_user_id is None:
			return view.error('Login required.', HTTP_401_UNAUTHORIZED)

		user_id = logged_user_id

	return view.user_images(user_id, db.get_all_user_images(user_id))


@app.route('/image', methods=('POST',))
def image_upload():
	user_id = session.get('user_id')

	if user_id is None:
		return view.error('Login required.', HTTP_401_UNAUTHORIZED)

	image_file  = request.files.get('file')
	image_title = request.form.get('title', '').strip()

	if image_file is None or not image_title:
		return view.error('Missing parameters.', HTTP_400_BAD_REQUEST)

	image_id = db.save_image(image_file, image_title, user_id)

	if not image_id:
		return view.error('Unsupported file type, only JPEG allowed.', HTTP_400_BAD_REQUEST)

	return view.upload_success(image_id, image_title, user_id)


@app.route('/image/<int:id>', methods=('GET', 'DELETE'))
def image(**urlparams):
	image_id = urlparams['id']

	details = db.get_image_details(image_id)
	if not details:
		abort(HTTP_404_NOT_FOUND)

	image_title, image_owner = details
	return view.image(image_id, image_title, image_owner)

@app.route('/image/<int:id>/download', methods=('GET', 'PUT', 'DELETE'))
def image_download(**urlparams):
	image_id = urlparams['id']

	image_path = db.get_image_path(image_id)
	if image_path is None:
		abort(HTTP_404_NOT_FOUND)

	return send_file(image_path)
