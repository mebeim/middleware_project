#!/usr/bin/env python3

import sys
from app import app

if __name__ == '__main__':
	print('Running:', *sys.argv)

	if '--prod' in sys.argv:
		context = ('https/fullchain.pem', 'https/privkey.pem')
		app.run(host='0.0.0.0', ssl_context=context)
	else:
		app.run(host='0.0.0.0')
