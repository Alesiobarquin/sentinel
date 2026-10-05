"""Public-client ChatGPT OAuth. Credentials never enter model context or audits.

One local account is supported initially. Use a separate credential directory to
select another account. No Codex credentials or private API routes are used.
"""

from contextlib import contextmanager
import base64
import fcntl
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import secrets
import tempfile
import time
from urllib.parse import parse_qs, urlencode, urlsplit
from uuid import uuid4
import webbrowser

import httpx
import jwt

ISSUER = "https://auth.openai.com"
AUTHORIZE = ISSUER + "/api/accounts/authorize"
TOKEN = ISSUER + "/api/accounts/oauth/token"
JWKS = ISSUER + "/.well-known/jwks.json"
RESOURCE = "https://api.openai.com/v1"
SCOPES = "openid profile email offline_access resource.invoke chatgpt.tokens.use.direct"
DEFAULT_DIR = Path.home() / ".config" / "sentinel"


class AuthError(RuntimeError):
    """Sanitized authentication failure; do not append token-endpoint bodies."""


def _request(url: str, *, form: dict | None = None, bearer: str | None = None) -> dict:
    headers = {"Authorization": "Bearer " + bearer} if bearer else {}
    try:
        with httpx.Client(timeout=15, follow_redirects=False) as client:
            with client.stream("POST" if form is not None else "GET", url, data=form, headers=headers) as response:
                if response.status_code != 200:
                    raise AuthError(f"OpenAI authentication request returned HTTP {response.status_code}; sign in again if necessary")
                chunks, size = [], 0
                for chunk in response.iter_bytes():
                    size += len(chunk)
                    if size > 1_000_000:
                        raise AuthError("Authentication response exceeded its size limit")
                    chunks.append(chunk)
        payload = json.loads(b"".join(chunks))
        if not isinstance(payload, dict):
            raise ValueError()
        return payload
    except (httpx.HTTPError, ValueError) as exc:
        raise AuthError("OpenAI authentication request failed or returned invalid JSON") from exc


class CredentialStore:
    def __init__(self, directory: Path = DEFAULT_DIR):
        self.directory = directory

    def prepare(self) -> None:
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.directory.is_symlink():
            raise AuthError("Credential directory cannot be a symbolic link")
        self.directory.chmod(0o700)

    def read(self, name: str) -> dict:
        path = self.directory / name
        if not path.exists():
            return {}
        if path.is_symlink() or path.stat().st_mode & 0o077:
            raise AuthError("Credential file must be owner-only and cannot be a symbolic link")
        try:
            with path.open() as stream:
                raw = stream.read(64_001)
            data = json.loads(raw)
            if len(raw) > 64_000 or not isinstance(data, dict):
                raise ValueError()
            return data
        except (OSError, ValueError) as exc:
            raise AuthError("Credential file is invalid; sign in again") from exc

    def write(self, name: str, data: dict) -> None:
        self.prepare()
        fd, temporary = tempfile.mkstemp(prefix=".pending-", dir=self.directory)
        try:
            with os.fdopen(fd, "w") as stream:
                json.dump(data, stream, allow_nan=False)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.directory / name)
        finally:
            Path(temporary).unlink(missing_ok=True)

    @contextmanager
    def lock(self):
        self.prepare()
        fd = os.open(self.directory / ".lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "w") as stream:
            fcntl.flock(stream, fcntl.LOCK_EX)
            yield

    def host_id(self) -> str:
        host = self.read("host.json")
        if not host:
            host = {"ext_agent_host_id": "urn:uuid:" + str(uuid4())}
            self.write("host.json", host)
        return host["ext_agent_host_id"]


def validate_identity(token: str, client_id: str, nonce: str | None, *, keys: dict | None = None) -> dict:
    try:
        header = jwt.get_unverified_header(token)
        if header.get("alg") != "RS256" or not isinstance(header.get("kid"), str):
            raise ValueError()
        jwks = keys if keys is not None else _request(JWKS)
        matching = [key for key in jwks["keys"] if key.get("kid") == header["kid"]]
        if len(matching) != 1:
            raise ValueError()
        key = jwt.PyJWK.from_dict(matching[0], algorithm="RS256").key
        claims = jwt.decode(token, key, algorithms=["RS256"], audience=client_id, issuer=ISSUER,
                            options={"require": ["sub", "iss", "aud", "exp", "iat"]})
        if not isinstance(claims["sub"], str) or not claims["sub"]:
            raise ValueError()
        if nonce is not None and not secrets.compare_digest(str(claims.get("nonce", "")), nonce):
            raise ValueError()
        return claims
    except (jwt.PyJWTError, ValueError, KeyError, TypeError) as exc:
        raise AuthError("OpenAI identity signature, issuer, audience, expiry, or nonce validation failed") from exc


def _credentials(payload: dict, registration: dict, *, nonce: str | None, previous: dict | None = None) -> dict:
    try:
        if payload["token_type"].lower() != "bearer":
            raise ValueError()
        scopes = payload["scope"].split()
        if not {"resource.invoke", "chatgpt.tokens.use.direct"} <= set(scopes):
            raise AuthError("Sign-in did not grant permission to use your ChatGPT plan")
        for name in ("access_token", "refresh_token", "id_token"):
            if not isinstance(payload[name], str) or not payload[name] or len(payload[name]) > 30_000:
                raise ValueError()
        expires = payload["expires_in"]
        if type(expires) is not int or not 0 < expires <= 86400:
            raise ValueError()
        claims = validate_identity(payload["id_token"], registration["client_id"], nonce)
        if previous and claims["sub"] != previous["subject"]:
            raise AuthError("Sign-in returned a different account; existing credentials were preserved")
        return {
            **registration, "subject": claims["sub"], "issuer": ISSUER,
            "access_token": payload["access_token"], "refresh_token": payload["refresh_token"],
            "id_token": payload["id_token"], "scopes": scopes,
            "saved_at": time.time(), "expires_at": time.time() + expires,
        }
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise AuthError("OpenAI returned an incomplete credential set") from exc


def callback_parameters(query: str, state: str, selected_client: str | None) -> tuple[str, str]:
    values = parse_qs(query, keep_blank_values=True, max_num_fields=12)
    if any(len(items) != 1 for items in values.values()):
        raise AuthError("Duplicate OAuth callback parameters")
    returned_state = values.get("state", [""])[0]
    if not secrets.compare_digest(returned_state, state):
        raise AuthError("OAuth state did not match the pending sign-in")
    if "error" in values:
        raise AuthError("Sign-in was declined or failed; no credentials were replaced")
    client = values.get("client_id", [selected_client or ""])[0]
    code = values.get("code", [""])[0]
    if not code or not client or client == "dynamic_agent_client" or len(code) > 4096 or len(client) > 256:
        raise AuthError("Sign-in callback did not supply a code and issued client ID")
    if selected_client and selected_client != client:
        raise AuthError("OAuth callback changed the selected client ID")
    return code, client


def login(store: CredentialStore, *, timeout: float = 300, open_browser=webbrowser.open) -> None:
    # Hold the account lock through sign-in to serialize credential replacement.
    with store.lock():
        previous = store.read("credentials.json")
        registration = store.read("registration.json")
        client = previous.get("client_id") or registration.get("client_id")
        host_id = store.host_id()
        state, nonce, verifier = (secrets.token_urlsafe(32) for _ in range(3))
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
        result = {}

        class Callback(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass  # Standard access logs contain the authorization code.

            def do_GET(self):
                parsed = urlsplit(self.path)
                if parsed.path != "/auth/callback" or len(self.path) > 12_000:
                    self.send_error(404)
                    return
                try:
                    code, issued = callback_parameters(parsed.query, state, client)
                    result.update(code=code, client_id=issued)
                    message = "Sign-in received. Return to Sentinel; identity validation is still required."
                    status = 200
                except (AuthError, ValueError) as exc:
                    # Reject invalid callbacks without consuming the valid pending attempt.
                    message, status = "Sign-in callback rejected.", 400
                    if "declined" in str(exc):
                        result["error"] = AuthError(str(exc))
                body = message.encode()
                self.send_response(status)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)

        class BoundedServer(HTTPServer):
            def get_request(self):
                connection, address = super().get_request()
                connection.settimeout(2)
                return connection, address

        with BoundedServer(("127.0.0.1", 0), Callback) as server:
            server.timeout = 1
            redirect = f"http://127.0.0.1:{server.server_port}/auth/callback"
            parameters = {
                "client_id": client or "dynamic_agent_client", "ext_agent_host_id": host_id,
                "response_type": "code", "redirect_uri": redirect, "scope": SCOPES,
                "resource": RESOURCE, "state": state, "nonce": nonce,
                "code_challenge_method": "S256", "code_challenge": challenge,
            }
            if not client:
                parameters["agent_name_hint"] = "Sentinel"
            # Deliberately omit id_token_hint to keep authorization URLs token-free.
            url = AUTHORIZE + "?" + urlencode(parameters)
            print("Continue with ChatGPT in your browser. Complete sign-in and the permission grant.", flush=True)
            if not open_browser(url):
                print("Browser could not open. Run login from a desktop terminal.", flush=True)
                raise AuthError("System browser could not start")
            deadline = time.monotonic() + timeout
            while not result and time.monotonic() < deadline:
                server.handle_request()
        if not result:
            raise AuthError("Sign-in timed out; no credentials were replaced")
        if "error" in result:
            raise result["error"]
        registration = {"client_id": result["client_id"], "ext_agent_host_id": host_id}
        store.write("registration.json", registration)
        payload = _request(TOKEN, form={
            "grant_type": "authorization_code", "client_id": result["client_id"],
            "code": result["code"], "code_verifier": verifier,
            "redirect_uri": redirect, "resource": RESOURCE,
        })
        store.write("credentials.json", _credentials(payload, registration, nonce=nonce, previous=previous))
        print("ChatGPT plan access validated. Credentials saved with owner-only permissions.")


def access_token(store: CredentialStore) -> str:
    with store.lock():
        current = store.read("credentials.json")
        if not current:
            raise AuthError("Run 'python -m sentinel login' to connect your ChatGPT plan")
        if not {"resource.invoke", "chatgpt.tokens.use.direct"} <= set(current.get("scopes", [])):
            raise AuthError("Stored sign-in does not grant ChatGPT plan usage")
        if current.get("expires_at", 0) <= time.time() + 60:
            payload = _request(TOKEN, form={
                "grant_type": "refresh_token", "client_id": current["client_id"],
                "refresh_token": current["refresh_token"], "resource": RESOURCE,
            })
            registration = {key: current[key] for key in ("client_id", "ext_agent_host_id")}
            current = _credentials(payload, registration, nonce=None, previous=current)
            store.write("credentials.json", current)
        return current["access_token"]


def available_models(store: CredentialStore) -> list[dict]:
    payload = _request(RESOURCE + "/models", bearer=access_token(store))
    try:
        models = payload["models"]
        if not isinstance(models, list):
            raise ValueError()
        visible = [{"slug": item["slug"], "display_name": item["display_name"]}
                   for item in models if item.get("visibility") == "list"]
        if not all(isinstance(v, str) for item in visible for v in item.values()):
            raise ValueError()
        return visible
    except (KeyError, TypeError, AttributeError, ValueError) as exc:
        raise AuthError("OpenAI returned an invalid account model catalog") from exc


def logout(store: CredentialStore) -> bool:
    confirmed = True
    with store.lock():
        current = store.read("credentials.json")
        if current:
            try:
                discovery = _request(ISSUER + "/.well-known/openid-configuration")
                endpoint = discovery["revocation_endpoint"]
                if urlsplit(endpoint).scheme != "https" or urlsplit(endpoint).hostname != "auth.openai.com":
                    raise AuthError("Unexpected revocation endpoint")
                with httpx.Client(timeout=15, follow_redirects=False) as client:
                    response = client.post(endpoint, data={
                        "token": current["refresh_token"], "token_type_hint": "refresh_token",
                        "client_id": current["client_id"],
                    })
                confirmed = response.status_code == 200
            except (AuthError, httpx.HTTPError, KeyError):
                confirmed = False
            (store.directory / "credentials.json").unlink(missing_ok=True)
    return confirmed
