import http.server
import socketserver
import os

PORT = 8081
DIRECTORY = "frontend"

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"🌐 BlackBook Frontend Server running at http://localhost:{PORT}")
        print(f"📁 Serving files from: {os.path.abspath(DIRECTORY)}")
        print("\n🎯 Access URLs:")
        print(f"   Admin Panel (God Mode): http://localhost:{PORT}/admin-panel.html")
        print(f"   Layer 1 Interface: http://localhost:{PORT}/blackbook-layer1.html")
        print(f"   Basic Interface: http://localhost:{PORT}/index.html")
        print("\n🚀 Make sure your BlackBook API server is running on localhost:3000")
        print("Press Ctrl+C to stop the server")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Frontend server stopped")