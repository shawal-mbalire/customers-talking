"""JWT validation for Neon Auth (Better Auth) tokens."""
import time
from functools import wraps

import jwt
import requests as http_requests
from flask import g, jsonify, request

_jwks_cache: dict = {"keys": [], "fetched_at": 0}
_JWKS_TTL = 3600


def _get_jwks(jwks_url: str) -> list:
    now = time.time()
    if _jwks_cache["keys"] and now - _jwks_cache["fetched_at"] < _JWKS_TTL:
        return _jwks_cache["keys"]
    resp = http_requests.get(jwks_url, timeout=10)
    resp.raise_for_status()
    keys = resp.json().get("keys", [])
    _jwks_cache.update({"keys": keys, "fetched_at": now})
    return keys


def _validate_token(token: str, jwks_url: str) -> dict:
    keys = _get_jwks(jwks_url)
    header = jwt.get_unverified_header(token)
    kid = header.get("kid")
    matching = [k for k in keys if k.get("kid") == kid] if kid else keys
    if not matching:
        raise jwt.InvalidTokenError("No matching JWKS key found")
    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(matching[0])
    return jwt.decode(token, public_key, algorithms=["RS256"])


def jwt_required(f):
    """Validate Neon Auth JWT from Authorization: Bearer header."""
    @wraps(f)
    def decorated(*args, **kwargs):
        from flask import current_app
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Not authenticated"}), 401
        token = auth_header[7:]
        jwks_url = current_app.config["NEON_AUTH_JWKS_URL"]
        try:
            payload = _validate_token(token, jwks_url)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except Exception:
            return jsonify({"error": "Invalid token"}), 401
        g.current_user = {"id": payload.get("sub"), "email": payload.get("email")}
        return f(*args, **kwargs)
    return decorated
