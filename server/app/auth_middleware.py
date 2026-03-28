"""JWT validation middleware using HS256 tokens signed with FLASK_SECRET_KEY."""
import jwt
from functools import wraps
from flask import g, jsonify, request


def jwt_required(f):
    """Validate a JWT from Authorization: Bearer header."""
    @wraps(f)
    def decorated(*args, **kwargs):
        from flask import current_app
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Not authenticated"}), 401
        token = auth_header[7:]
        try:
            payload = jwt.decode(
                token,
                current_app.config["SECRET_KEY"],
                algorithms=["HS256"],
            )
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except Exception:
            return jsonify({"error": "Invalid token"}), 401
        g.current_user = {"id": payload.get("sub"), "email": payload.get("email")}
        return f(*args, **kwargs)
    return decorated
