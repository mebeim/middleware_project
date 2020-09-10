#!/usr/bin/env python3

import sys
import requests
import xml.etree.ElementTree as et
from time import sleep
from subprocess import Popen, PIPE
from urllib.parse import quote
from collections import defaultdict

BASE_URL         = sys.argv[1] if len(sys.argv) == 2 else 'http://127.0.0.1'
TEST_IMAGE       = 'test.jpg'
TEST_USER_A      = {'id': 'a', 'name': 'Asd Fghjkl', 'password': 'test_a'}
TEST_USER_B      = {'id': 'b', 'name': 'Bnm Zxcv', 'password': 'test_b'}
TEST_USER_A_AUTH = (TEST_USER_A['id'], TEST_USER_A['password'])
TEST_USER_B_AUTH = (TEST_USER_B['id'], TEST_USER_B['password'])

TEST_OAUTH_CLIENT_CALLBACK_PORT = 9999

TEST_OAUTH_CLIENT = {
	'name'        : 'Test Client',
	'redirect_uri': f'http://127.0.0.1:{TEST_OAUTH_CLIENT_CALLBACK_PORT}/ok'
}

TEST_OAUTH_REQUEST_PARAMS = {
	'response_type': 'token',
	'response_mode': 'fragment',
	'client_id'    : None,
	'scopes'       : None,
	'redirect_uri' : TEST_OAUTH_CLIENT['redirect_uri']
}

tests            = []
images           = defaultdict(list)
client_id        = None
user_token_read  = None
user_token_write = None


### UTILITY FUNCTIONS ##########################################################

def test(f):
	global tests
	tests.append(f)
	return f


def expect(expected_code, method, path, token=None, *args, **kwargs):
	if token is None:
		r = method(path, *args, **kwargs)
	else:
		r = method(path, headers={'Authorization': f'Bearer {token}'}, *args, **kwargs)

	assert r.status_code == expected_code
	return r


def get(path, *args, **kwargs):
	return requests.get(BASE_URL + path, *args, **kwargs)


def post(path, *args, **kwargs):
	return requests.post(BASE_URL + path, *args, **kwargs)


def delete(path, *args, **kwargs):
	return requests.delete(BASE_URL + path, *args, **kwargs)


def extract(resp, xpath):
	root = et.fromstring(resp.text)
	return root.findtext(xpath)


def extract_all(resp, xpath):
	for el in et.fromstring(resp.text).findall(xpath):
		yield el.text


### UNIT TESTS #################################################################

@test
def user_registration_success():
	expect(200, post, '/register', data=TEST_USER_A)
	expect(200, post, '/register', data=TEST_USER_B)


@test
def user_registration_already_registered():
	expect(403, post, '/register', data=TEST_USER_A)

	d = TEST_USER_A
	d.update({'password': 'new_pw'})
	expect(403, post, '/register', data=d)


@test
def user_registration_missing_paramaeters():
	expect(400, post, '/register', data={'id': 'x', 'name': 'x'})
	expect(400, post, '/register', data={'id': 'x', 'password': 'x'})
	expect(400, post, '/register', data={'name': 'x', 'password': 'x'})


@test
def user_registration_invalid_parameters():
	expect(400, post, '/register', data={'id': 'x?', 'name': 'x', 'password': 'x'})
	expect(400, post, '/register', data={'id': 'x', 'name': 'x?', 'password': 'x'})
	expect(400, post, '/register', data={'id': '', 'name': 'x', 'password': 'x'})
	expect(400, post, '/register', data={'id': 'x', 'name': '', 'password': 'x'})


@test
def user_delete():
	expect(200, delete, '/user/' + TEST_USER_B['id'], auth=TEST_USER_B_AUTH)
	expect(200, post, '/register', data=TEST_USER_B)


@test
def user_delete_other():
	expect(403, delete, '/user/xxx', auth=TEST_USER_A_AUTH)


@test
def user_get():
	r = expect(200, get, '/user/' + TEST_USER_A['id'], auth=TEST_USER_A_AUTH)
	assert extract(r, 'name') == TEST_USER_A['name']

	r = expect(200, get, '/user/' + TEST_USER_B['id'], auth=TEST_USER_A_AUTH)
	assert extract(r, 'name') == TEST_USER_B['name']


@test
def user_list():
	r = expect(200, get, '/users', auth=TEST_USER_A_AUTH)
	assert set(extract_all(r, 'user/id')) == {TEST_USER_A['id'], TEST_USER_B['id']}


@test
def image_upload():
	global images

	for i in range(1, 4):
		with open(TEST_IMAGE, 'rb') as f:
			r = expect(200, post, '/upload', auth=TEST_USER_A_AUTH, files={'file': f}, data={'title': f'Amazing test image {i}!'})
			img_id = extract(r, 'id')
			images[TEST_USER_A['id']].append(img_id)

			f.seek(0)
			r = expect(200, post, '/upload', auth=TEST_USER_B_AUTH, files={'file': f}, data={'title': f'Amazing test image {i}!'})
			img_id = extract(r, 'id')
			images[TEST_USER_B['id']].append(img_id)


@test
def image_list():
	for user_id, known_ids in images.items():
		if not known_ids:
			continue

		r = expect(200, get, f'/user/{user_id}/images', auth=TEST_USER_A_AUTH)
		assert set(extract_all(r, 'image/id')) == set(known_ids)


@test
def image_download():
	for user_id, image_ids in images.items():
		for image_id in image_ids:
			r = expect(200, get, f'/image/{image_id}', auth=TEST_USER_A_AUTH)
			download_link = extract(r, 'link[@rel="download"]')

			r = requests.get(download_link, auth=TEST_USER_A_AUTH)
			assert r.status_code == 200


@test
def image_delete():
	image_id = max(images[TEST_USER_A['id']])
	r = expect(200, delete, f'/image/{image_id}', auth=TEST_USER_A_AUTH)


@test
def oauth_client_registration():
	global client_id
	r = expect(200, post, '/oauth/register-client', data=TEST_OAUTH_CLIENT)
	client_id = extract(r, 'id')
	extract(r, 'secret')


@test
def oauth_authorize():
	global user_token_read
	global user_token_write

	client = Popen(['./test_client.py', str(TEST_OAUTH_CLIENT_CALLBACK_PORT)], stdout=PIPE)
	sleep(0.5)

	params = TEST_OAUTH_REQUEST_PARAMS
	params.update({'client_id': client_id, 'scopes': 'read'})
	url = '/oauth/authorize?' + '&'.join(map(lambda kv: f'{kv[0]}={quote(kv[1])}', params.items()))
	expect(200, get, url, auth=TEST_USER_A_AUTH)

	params.update({'scopes': 'write'})
	url = '/oauth/authorize?' + '&'.join(map(lambda kv: f'{kv[0]}={quote(kv[1])}', params.items()))
	expect(200, get, url, auth=TEST_USER_A_AUTH)

	client.terminate()
	out, _ = client.communicate()

	user_token_read, user_token_write = out.decode().splitlines()
	assert user_token_read
	assert user_token_write


@test
def oauth_authorize_invalid_scopes():
	params = TEST_OAUTH_REQUEST_PARAMS
	params.update({'redirect_uri': 'http://evil.com/ok'})
	params.update({'client_id': client_id, 'scopes': 'lol'})
	url = '/oauth/authorize?' + '&'.join(map(lambda kv: f'{kv[0]}={quote(kv[1])}', params.items()))

	expect(400, get, url, auth=TEST_USER_A_AUTH)


@test
def oauth_authorize_invalid_redirect_uri():
	params = TEST_OAUTH_REQUEST_PARAMS
	params.update({'redirect_uri': 'http://evil.com/ok'})
	params.update({'client_id': client_id, 'scopes': 'read'})
	url = '/oauth/authorize?' + '&'.join(map(lambda kv: f'{kv[0]}={quote(kv[1])}', params.items()))

	expect(400, get, url, auth=TEST_USER_A_AUTH)


@test
def oauth_get_client():
	expect(200, get, f'/oauth/client/{client_id}', auth=TEST_USER_A_AUTH)
	expect(200, get, f'/oauth/client/{client_id}', token=user_token_read)


@test
def oauth_no_token():
	expect(401, get, f'/oauth/client/{client_id}', token='')


@test
def oauth_get_image():
	image_id = images[TEST_USER_A['id']][0]
	expect(200, get, f'/image/{image_id}', token=user_token_read)
	expect(200, get, f'/image/{image_id}', token=user_token_write)


@test
def oauth_get_image_other_user():
	image_id = images[TEST_USER_B['id']][0]
	expect(403, get, f'/image/{image_id}' , token=user_token_read)
	expect(403, get, f'/image/{image_id}' , token=user_token_write)


@test
def oauth_delete_image():
	image_id = images[TEST_USER_A['id']][0]
	expect(403, delete, f'/image/{image_id}', token=user_token_read)
	expect(200, delete, f'/image/{image_id}', token=user_token_write)


### MAIN #######################################################################

if __name__ == '__main__':
	pad = max(map(lambda t: len(t.__name__), tests))

	for t in tests:
		ex = None
		print(f'{t.__name__}'.ljust(pad), end=' ', flush=True)

		try:
			t()
		except Exception as e:
			ex = e

		if ex is None:
			print('\x1b[32mOK\x1b[0m')
		else:
			print('\x1b[31mFAILED\x1b[0m')
			raise ex

