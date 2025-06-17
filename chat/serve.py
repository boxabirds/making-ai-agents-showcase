#\!/usr/bin/env python3
import http.server
import socketserver
import os

PORT = 8082
os.chdir(os.path.dirname(os.path.abspath(__file__)))

Handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Server running at http://localhost:{PORT}/")
    print("Open this URL in your browser to view the chat interface")
    print("Press Ctrl+C to stop the server")
    httpd.serve_forever()
