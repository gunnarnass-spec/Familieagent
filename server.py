import http.server
import urllib.request
import urllib.error
import json
import os
import sys

PORT = int(os.environ.get('PORT', 8765))
API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')

# Fall back to apikey.txt for local use
if not API_KEY:
    try:
        with open('apikey.txt', 'r', encoding='utf-8') as f:
            API_KEY = f.read().strip()
    except:
        pass

class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        print(format % args, flush=True)

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if self.path == '/' or self.path == '':
            self.path = '/familieagent.html'
        # Set correct content types
        if self.path.endswith('.json'):
            self.path = self.path
        super().do_GET()

    def guess_type(self, path):
        if path.endswith('.json'): return 'application/json'
        if path.endswith('.js'): return 'application/javascript'
        if path.endswith('.png'): return 'image/png'
        return super().guess_type(path)

    def do_POST(self):
        if self.path == '/api':
            try:
                if not API_KEY:
                    self._json_error(500, 'API-nøkkel mangler. Sett ANTHROPIC_API_KEY miljøvariabel.')
                    return

                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length)

                req = urllib.request.Request(
                    'https://api.anthropic.com/v1/messages',
                    data=body,
                    headers={
                        'Content-Type': 'application/json',
                        'x-api-key': API_KEY,
                        'anthropic-version': '2023-06-01'
                    },
                    method='POST'
                )

                with urllib.request.urlopen(req, timeout=30) as resp:
                    result = resp.read()

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self._cors()
                self.end_headers()
                self.wfile.write(result)

            except urllib.error.HTTPError as e:
                error_body = e.read()
                print(f'Anthropic feil {e.code}: {error_body.decode()}', flush=True)
                self.send_response(e.code)
                self.send_header('Content-Type', 'application/json')
                self._cors()
                self.end_headers()
                self.wfile.write(error_body)

            except Exception as e:
                print(f'Feil: {e}', flush=True)
                self._json_error(500, str(e))
        else:
            self._json_error(404, 'Ikke funnet')

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def _json_error(self, code, msg):
        body = json.dumps({'error': {'message': msg}}).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self._cors()
        self.end_headers()
        self.wfile.write(body)

if __name__ == '__main__':
    print(f'Server starter på port {PORT}', flush=True)
    if API_KEY:
        print(f'API-nøkkel: {API_KEY[:12]}... ({len(API_KEY)} tegn)', flush=True)
    else:
        print('ADVARSEL: Ingen API-nøkkel funnet!', flush=True)
    with http.server.HTTPServer(('', PORT), Handler) as httpd:
        httpd.serve_forever()
