"""One-time Strava OAuth setup. Run this once to authorize the app."""
import os
import json
import webbrowser
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8080/callback"
TOKEN_FILE = "strava_tokens.json"

_auth_code = None


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global _auth_code
        params = parse_qs(urlparse(self.path).query)
        if "code" in params:
            _auth_code = params["code"][0]
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"<h2>Authorized! You can close this tab.</h2>")
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"<h2>Authorization failed. Check the terminal.</h2>")

    def log_message(self, *args):
        pass


def main():
    auth_url = (
        f"https://www.strava.com/oauth/authorize"
        f"?client_id={CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={REDIRECT_URI}"
        f"&approval_prompt=force"
        f"&scope=activity:read_all"
    )

    print("Opening Strava in your browser for authorization...")
    print(f"If it doesn't open automatically, visit:\n{auth_url}\n")
    webbrowser.open(auth_url)

    print("Waiting for you to authorize in the browser...")
    HTTPServer(("localhost", 8080), CallbackHandler).handle_request()

    if not _auth_code:
        print("Authorization failed.")
        return

    print("Exchanging code for tokens...")
    resp = requests.post("https://www.strava.com/oauth/token", data={
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": _auth_code,
        "grant_type": "authorization_code",
    })

    if resp.status_code != 200:
        print(f"Token exchange failed: {resp.text}")
        return

    data = resp.json()
    with open(TOKEN_FILE, "w") as f:
        json.dump({
            "access_token": data["access_token"],
            "refresh_token": data["refresh_token"],
            "expires_at": data["expires_at"],
        }, f)

    athlete = data.get("athlete", {})
    print(f"\nSuccess! Authorized as: {athlete.get('firstname', '')} {athlete.get('lastname', '')}")
    print(f"Tokens saved to {TOKEN_FILE}")


if __name__ == "__main__":
    main()
