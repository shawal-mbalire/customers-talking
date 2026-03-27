from flask import Blueprint, jsonify, request
from ..services import human_queue

sessions_bp = Blueprint("sessions", __name__)


@sessions_bp.get("/sessions/escalated")
def get_escalated_sessions():
    """Return all sessions waiting for a human agent."""
    return jsonify(human_queue.get_all())


@sessions_bp.delete("/sessions/escalated/<session_id>")
def resolve_session(session_id: str):
    """Mark a session as resolved (remove from queue)."""
    removed = human_queue.remove(session_id)
    if removed:
        return jsonify({"message": "Session resolved.", "sessionId": session_id})
    return jsonify({"error": "Session not found."}), 404
