from flask import Blueprint, jsonify, request
from ..services import human_queue, session_store

sessions_bp = Blueprint("sessions", __name__)


@sessions_bp.get("/sessions")
def get_sessions():
    """Return sessions with optional ?status= and ?channel= filters."""
    status = request.args.get("status")
    channel = request.args.get("channel")
    return jsonify(session_store.get_filtered(status=status, channel=channel))


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
