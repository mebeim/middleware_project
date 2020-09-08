#!/usr/bin/env python3

import sys
from app import app

if __name__ == '__main__':
	print('Running:', *sys.argv, file=sys.stderr)

	if '--test' in sys.argv:
		app.run(host='0.0.0.0', port=5001)
	else:
		context = ('https/fullchain.pem', 'https/privkey.pem')
		app.run(host='0.0.0.0', port=5000, ssl_context=context)
