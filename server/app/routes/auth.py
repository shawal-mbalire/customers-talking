from flask import Blueprint, jsonify, g
from ..auth_middleware import jwt_required

auth_bp = Blueprint("auth", __name__)


@auth_bp.get("/api/auth/me")
@jwt_required
def me():
    return jsonify({"id": g.current_user["id"], "email": g.current_user["email"]})
