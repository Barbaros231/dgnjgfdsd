#!/usr/bin/env python3
"""
Simple auth server for Fatowin modified site.
Serves the HTML and provides /api/register and /api/login with username/password.
Users stored in users.json on disk (server-side persistence).
"""

import json
import os
import hashlib
import secrets
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timezone

PORT = 8080
USERS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.json")
SESSIONS = {}  # token -> username (in-memory, survives while server runs)

def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return salt, h

def verify_password(password, salt, stored_hash):
    _, h = hash_password(password, salt)
    return h == stored_hash

class AuthHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.dirname(os.path.abspath(__file__)), **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length else "{}"
        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            data = {}

        if path == "/api/register":
            self.handle_register(data)
        elif path == "/api/login":
            self.handle_login(data)
        elif path == "/api/logout":
            self.handle_logout()
        elif path == "/api/me":
            self.handle_me()
        else:
            self.send_error(404, "Not Found")

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/me":
            self.handle_me()
        elif parsed.path == "/api/users-count":
            users = load_users()
            self.send_json({"count": len(users)})
        else:
            # Serve static files (index.html etc.)
            super().do_GET()

    def send_json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def handle_register(self, data):
        username = (data.get("username") or "").strip()
        password = data.get("password") or ""

        if not username or len(username) < 3:
            return self.send_json({"ok": False, "error": "Username must be at least 3 characters"}, 400)
        if not password or len(password) < 4:
            return self.send_json({"ok": False, "error": "Password must be at least 4 characters"}, 400)
        if not username.isalnum() and "_" not in username and "-" not in username:
            # allow alphanumeric + _ -
            if not all(c.isalnum() or c in "_-" for c in username):
                return self.send_json({"ok": False, "error": "Username may only contain letters, numbers, _ and -"}, 400)

        users = load_users()
        if username.lower() in {u.lower() for u in users}:
            return self.send_json({"ok": False, "error": "Username already taken"}, 409)

        salt, pw_hash = hash_password(password)
        users[username] = {
            "username": username,
            "salt": salt,
            "password_hash": pw_hash,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "balance": 1000.0,  # welcome bonus in play money
            "last_login": None,
        }
        save_users(users)

        token = secrets.token_hex(32)
        SESSIONS[token] = username

        self.send_json({
            "ok": True,
            "message": "Registration successful",
            "token": token,
            "user": {"username": username, "balance": 1000.0, "created_at": users[username]["created_at"]}
        })

    def handle_login(self, data):
        username = (data.get("username") or "").strip()
        password = data.get("password") or ""

        if not username or not password:
            return self.send_json({"ok": False, "error": "Username and password required"}, 400)

        users = load_users()
        # case-insensitive lookup
        real_username = None
        for u in users:
            if u.lower() == username.lower():
                real_username = u
                break

        if not real_username:
            return self.send_json({"ok": False, "error": "Invalid username or password"}, 401)

        user = users[real_username]
        if not verify_password(password, user["salt"], user["password_hash"]):
            return self.send_json({"ok": False, "error": "Invalid username or password"}, 401)

        user["last_login"] = datetime.now(timezone.utc).isoformat()
        save_users(users)

        token = secrets.token_hex(32)
        SESSIONS[token] = real_username

        self.send_json({
            "ok": True,
            "message": "Login successful",
            "token": token,
            "user": {
                "username": real_username,
                "balance": user.get("balance", 0),
                "created_at": user.get("created_at"),
                "last_login": user["last_login"]
            }
        })

    def handle_logout(self):
        auth = self.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
            SESSIONS.pop(token, None)
        self.send_json({"ok": True})

    def handle_me(self):
        auth = self.headers.get("Authorization", "")
        token = None
        if auth.startswith("Bearer "):
            token = auth[7:]
        # also check cookie-style query or body, but mainly header

        if not token or token not in SESSIONS:
            return self.send_json({"ok": False, "error": "Not authenticated"}, 401)

        username = SESSIONS[token]
        users = load_users()
        if username not in users:
            return self.send_json({"ok": False, "error": "User not found"}, 401)

        user = users[username]
        self.send_json({
            "ok": True,
            "user": {
                "username": username,
                "balance": user.get("balance", 0),
                "created_at": user.get("created_at"),
                "last_login": user.get("last_login")
            }
        })

    def log_message(self, format, *args):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {args[0]}")

def main():
    # ensure users.json exists
    if not os.path.exists(USERS_FILE):
        save_users({})
    print(f"Serving Fatowin on http://0.0.0.0:{PORT}")
    print(f"Users file: {USERS_FILE}")
    print("Endpoints: POST /api/register, POST /api/login, GET/POST /api/me, POST /api/logout")
    server = HTTPServer(("0.0.0.0", PORT), AuthHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down")
        server.shutdown()

if __name__ == "__main__":
    main()
