import uuid
import bcrypt
import jwt
from datetime import datetime, timezone, timedelta

from flask import Blueprint, jsonify, request, g, current_app

from ..db import get_cursor
from ..auth_middleware import jwt_required

auth_bp = Blueprint("auth", __name__)


def _make_token(user_id: str, email: str, secret: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


@auth_bp.post("/api/auth/sign-up")
def sign_up():
    data = request.get_json(force=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    name = (data.get("name") or "").strip()

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400

    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    user_id = str(uuid.uuid4())

    try:
        with get_cursor() as cur:
            cur.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cur.fetchone():
                return jsonify({"error": "Email already registered"}), 409
            cur.execute(
                "INSERT INTO users (id, email, name, password_hash) VALUES (%s, %s, %s, %s)",
                (user_id, email, name, pw_hash),
            )
    except Exception:
        return jsonify({"error": "Registration failed — please try again"}), 500

    token = _make_token(user_id, email, current_app.config["SECRET_KEY"])
    return jsonify({"token": token, "user": {"id": user_id, "email": email, "name": name}}), 201


@auth_bp.post("/api/auth/sign-in")
def sign_in():
    data = request.get_json(force=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    with get_cursor() as cur:
        cur.execute(
            "SELECT id, email, name, password_hash FROM users WHERE email = %s",
            (email,),
        )
        user = cur.fetchone()

    if not user or not bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
        return jsonify({"error": "Invalid email or password"}), 401

    token = _make_token(str(user["id"]), user["email"], current_app.config["SECRET_KEY"])
    return jsonify({
        "token": token,
        "user": {"id": str(user["id"]), "email": user["email"], "name": user.get("name", "")},
    })


@auth_bp.get("/api/auth/me")
@jwt_required
def me():
    return jsonify({"id": g.current_user["id"], "email": g.current_user["email"]})


@auth_bp.post("/api/auth/sign-out")
def sign_out():
    # JWT auth — client drops the token from localStorage
    return jsonify({"status": "ok"})
