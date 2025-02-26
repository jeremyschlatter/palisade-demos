#!/usr/bin/env python3
"""
Simple HTTP server for the LLM Prediction Viewer application.
Run this script to start a local server on port 8000.
"""

import http.server
import socketserver
import webbrowser
import os
import sys

PORT = 8000

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

def main():
    # Start the server
    handler = MyHandler
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"Server started at http://localhost:{PORT}")
        print("Press Ctrl+C to stop the server.")

        # Open the browser
        webbrowser.open(f"http://localhost:{PORT}")

        # Keep the server running
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")

if __name__ == "__main__":
    main()
