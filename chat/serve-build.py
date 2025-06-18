
#!/usr/bin/env python3
import http.server
import socketserver
import os

PORT = 8080
BUILD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build')

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BUILD_DIR, **kwargs)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

if __name__ == "__main__":
    if not os.path.exists(BUILD_DIR):
        print(f"Error: Build directory '{BUILD_DIR}' does not exist.")
        print("Please run the build script first: ./build.sh")
        exit(1)
    
    with socketserver.TCPServer(("0.0.0.0", PORT), MyHTTPRequestHandler) as httpd:
        print(f"Server running at http://0.0.0.0:{PORT}/")
        print(f"Serving files from: {BUILD_DIR}")
        print("Press Ctrl+C to stop")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped")
