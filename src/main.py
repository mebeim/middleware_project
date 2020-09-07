#!/usr/bin/env python3

import sys
from app import app

if __name__ == '__main__':
	print('Running:', *sys.argv)
	app.run(host='0.0.0.0')
