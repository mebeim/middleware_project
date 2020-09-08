#!/usr/bin/env python3

import sys
import re
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer

PORT = int(sys.argv[1])

class GetHandler(SimpleHTTPRequestHandler):
	def do_GET(self):
		print(re.findall(r'ok\?token=([0-9a-f]{128})', self.requestline)[0], flush=True)
		self.send_response(200)
		self.end_headers()
		self.wfile.write(b'Ok!')

	def log_message(self, *_):
		return

TCPServer.allow_reuse_address = True
srv = TCPServer(('localhost', PORT), GetHandler)
srv.serve_forever()
