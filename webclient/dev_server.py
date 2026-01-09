#!/usr/bin/env python3
"""
Development web server with no-cache headers to prevent browser caching issues
"""
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
import sys

class NoCacheHTTPRequestHandler(SimpleHTTPRequestHandler):
    """HTTP request handler that sends no-cache headers for all files"""
    
    def end_headers(self):
        # Add no-cache headers for development
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def log_message(self, format, *args):
        # Suppress some of the verbose logging
        if 'favicon.ico' not in args[0]:
            super().log_message(format, *args)


def run(port=8000, directory='.'):
    """Run the development server"""
    os.chdir(directory)
    
    server_address = ('', port)
    httpd = HTTPServer(server_address, NoCacheHTTPRequestHandler)
    
    print(f"Starting development server on http://localhost:{port}")
    print(f"Serving directory: {os.path.abspath(directory)}")
    print("Files are served with no-cache headers - browser won't cache them")
    print("Press Ctrl+C to stop the server\n")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
        sys.exit(0)


if __name__ == '__main__':
    # Get directory from command line or use current directory
    directory = sys.argv[1] if len(sys.argv) > 1 else '.'
    run(port=8000, directory=directory)
