import json
from http.server import BaseHTTPRequestHandler, HTTPServer


HOST = "127.0.0.1"
PORT = 8765


class FakeMCPHandler(BaseHTTPRequestHandler):
    def _write_json(self, body: dict, status: int = 200):
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if self.path != "/mcp":
            self._write_json({"error": "Not Found"}, status=404)
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length)

        try:
            req = json.loads(raw_body.decode("utf-8"))
        except Exception:
            self._write_json({"error": "Invalid JSON"}, status=400)
            return

        method = req.get("method")
        req_id = req.get("id")
        params = req.get("params", {})

        if method == "tools/call":
            name = params.get("name")
            arguments = params.get("arguments", {})

            if name == "weather":
                city = arguments.get("city", "Unknown")
                result = {
                    "content": [
                        {
                            "type": "text",
                            "text": f"{city} 今日天气: 晴, 26°C (fake data)",
                        }
                    ],
                    "isError": False,
                }
            else:
                result = {
                    "content": [
                        {
                            "type": "text",
                            "text": f"unknown tool: {name}",
                        }
                    ],
                    "isError": True,
                }

            self._write_json(
                {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": result,
                }
            )
            return

        self._write_json(
            {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": "Method not found"},
            },
            status=400,
        )


def run_server():
    server = HTTPServer((HOST, PORT), FakeMCPHandler)
    print(f"Fake MCP server running at http://{HOST}:{PORT}/mcp")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
