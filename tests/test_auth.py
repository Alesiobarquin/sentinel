import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlencode, urlsplit
from urllib.request import urlopen

from cryptography.hazmat.primitives.asymmetric import rsa
import jwt

from sentinel.auth import (
    AuthError, CredentialStore, ISSUER, _credentials, access_token,
    callback_parameters, login, validate_identity,
)


class OAuthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(cls.key.public_key()))
        cls.keys = {"keys": [{**public, "kid": "test-key", "alg": "RS256"}]}

    def token(self, **changes):
        claims = {"iss": ISSUER, "aud": "issued", "sub": "account", "nonce": "nonce",
                  "iat": int(time.time()), "exp": int(time.time()) + 300, **changes}
        return jwt.encode(claims, self.key, algorithm="RS256", headers={"kid": "test-key"})

    def test_identity_rejects_invalid_claims_and_signature(self):
        self.assertEqual(validate_identity(self.token(), "issued", "nonce", keys=self.keys)["sub"], "account")
        for changes in ({"iss": "https://attacker.invalid"}, {"aud": "another"},
                        {"exp": int(time.time()) - 1}, {"nonce": "other"}, {"sub": ""}):
            with self.subTest(changes=changes), self.assertRaises(AuthError):
                validate_identity(self.token(**changes), "issued", "nonce", keys=self.keys)
        other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        bad = jwt.encode({"sub": "account"}, other, algorithm="RS256", headers={"kid": "test-key"})
        with self.assertRaises(AuthError):
            validate_identity(bad, "issued", "nonce", keys=self.keys)

    def test_callback_state_client_and_duplicate_validation(self):
        self.assertEqual(callback_parameters("state=s&code=c&client_id=issued", "s", None), ("c", "issued"))
        self.assertEqual(callback_parameters("state=s&code=c", "s", "issued"), ("c", "issued"))
        for query in ("state=other&code=c&client_id=issued", "state=s&code=c",
                      "state=s&code=c&client_id=dynamic_agent_client", "state=s&code=c&code=d",
                      "state=s&code=c&client_id=other", "state=s&error=access_denied"):
            with self.subTest(query=query), self.assertRaises(AuthError):
                callback_parameters(query, "s", "issued" if "other" in query else None)

    def test_permission_and_account_validation_before_storage(self):
        registration = {"client_id": "issued", "ext_agent_host_id": "host"}
        payload = {"token_type": "Bearer", "access_token": "access", "refresh_token": "refresh",
                   "id_token": self.token(), "scope": "resource.invoke chatgpt.tokens.use.direct", "expires_in": 3600}
        with patch("sentinel.auth._request", return_value=self.keys):
            result = _credentials(payload, registration, nonce="nonce")
            self.assertEqual(result["subject"], "account")
            with self.assertRaises(AuthError):
                _credentials({**payload, "scope": "openid email"}, registration, nonce="nonce")
            with self.assertRaises(AuthError):
                _credentials(payload, registration, nonce="nonce", previous={"subject": "another"})

    def test_protected_storage_and_rotating_refresh(self):
        with tempfile.TemporaryDirectory() as directory:
            store = CredentialStore(Path(directory) / "auth")
            host = store.host_id()
            self.assertEqual(host, store.host_id())
            current = {"client_id": "issued", "ext_agent_host_id": host, "subject": "account",
                       "access_token": "old", "refresh_token": "old-refresh", "expires_at": 0,
                       "scopes": ["resource.invoke", "chatgpt.tokens.use.direct"]}
            store.write("credentials.json", current)
            self.assertEqual((store.directory / "credentials.json").stat().st_mode & 0o777, 0o600)
            self.assertEqual(store.directory.stat().st_mode & 0o777, 0o700)
            payload = {"token_type": "Bearer", "access_token": "new", "refresh_token": "replacement",
                       "id_token": self.token(), "scope": "resource.invoke chatgpt.tokens.use.direct", "expires_in": 3600}
            with patch("sentinel.auth._request", side_effect=[payload, self.keys]) as request:
                self.assertEqual(access_token(store), "new")
                self.assertEqual(request.call_args_list[0].kwargs["form"]["client_id"], "issued")
            self.assertEqual(store.read("credentials.json")["refresh_token"], "replacement")
            (store.directory / "credentials.json").chmod(0o644)
            with self.assertRaises(AuthError):
                store.read("credentials.json")

    def test_full_loopback_sign_in_uses_issued_client_pkce_and_exact_redirect(self):
        with tempfile.TemporaryDirectory() as directory:
            store = CredentialStore(Path(directory) / "auth")
            authorization, requests, threads = {}, [], []
            def browser(url):
                parameters = parse_qs(urlsplit(url).query)
                authorization.update({key: value[0] for key, value in parameters.items()})
                def return_callback():
                    target = authorization["redirect_uri"] + "?" + urlencode({
                        "state": authorization["state"], "code": "test-code", "client_id": "issued"})
                    with urlopen(target, timeout=3) as response:
                        response.read()
                thread = threading.Thread(target=return_callback)
                thread.start()
                threads.append(thread)
                return True
            def network(url, **kwargs):
                requests.append((url, kwargs))
                if url.endswith("jwks.json"):
                    return self.keys
                return {"token_type": "Bearer", "access_token": "access", "refresh_token": "refresh",
                        "id_token": self.token(nonce=authorization["nonce"]),
                        "scope": "resource.invoke chatgpt.tokens.use.direct", "expires_in": 3600}
            with patch("sentinel.auth._request", side_effect=network):
                login(store, timeout=5, open_browser=browser)
            for thread in threads:
                thread.join(timeout=3)
            self.assertEqual(authorization["client_id"], "dynamic_agent_client")
            self.assertEqual(authorization["agent_name_hint"], "Sentinel")
            self.assertEqual(authorization["code_challenge_method"], "S256")
            form = requests[0][1]["form"]
            self.assertEqual(form["client_id"], "issued")
            self.assertEqual(form["redirect_uri"], authorization["redirect_uri"])
            self.assertNotIn("client_secret", form)
            self.assertEqual(store.read("credentials.json")["subject"], "account")


if __name__ == "__main__":
    unittest.main()
