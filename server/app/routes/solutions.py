from flask import Blueprint, jsonify, request
from ..services import solutions_store
from ..auth_middleware import jwt_required

solutions_bp = Blueprint("solutions", __name__)


@solutions_bp.get("/solutions")
@jwt_required
def list_solutions():
    return jsonify(solutions_store.get_all())


@solutions_bp.post("/solutions")
@jwt_required
def create_solution():
    data = request.get_json(force=True)
    solution = solutions_store.create(data)
    return jsonify(solution.to_dict()), 201


@solutions_bp.put("/solutions/<solution_id>")
@jwt_required
def update_solution(solution_id: str):
    data = request.get_json(force=True)
    solution = solutions_store.update(solution_id, data)
    if solution:
        return jsonify(solution.to_dict())
    return jsonify({"error": "Solution not found."}), 404


@solutions_bp.delete("/solutions/<solution_id>")
@jwt_required
def delete_solution(solution_id: str):
    deleted = solutions_store.delete(solution_id)
    if deleted:
        return jsonify({"message": "Deleted.", "id": solution_id})
    return jsonify({"error": "Solution not found."}), 404
