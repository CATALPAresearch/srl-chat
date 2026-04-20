"""Interview protocol CRUD routes."""
import json
import os
import glob

from flask import Blueprint, request, jsonify, send_from_directory
from flask_cors import cross_origin

from ._paths import CONFIG_DIR

protocols_bp = Blueprint('protocols', __name__)

_INTERVIEW_DIR = os.path.join(CONFIG_DIR, "interview")


@protocols_bp.route("/protocols", methods=["GET"])
@cross_origin()
def list_protocols():
    """List all available interview protocols."""
    try:
        protocol_files = glob.glob(os.path.join(_INTERVIEW_DIR, "*.json"))
        protocols = [
            {"name": os.path.splitext(os.path.basename(f))[0], "filename": os.path.basename(f)}
            for f in protocol_files
        ]
        return jsonify(protocols), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@protocols_bp.route("/protocols/<name>", methods=["GET"])
@cross_origin()
def get_protocol(name):
    """Get a specific interview protocol by name."""
    try:
        safe_name = os.path.basename(name)
        path = os.path.join(_INTERVIEW_DIR, f"{safe_name}.json")
        if not os.path.isfile(path):
            return jsonify({"error": "Protocol not found"}), 404
        with open(path, "r", encoding="utf-8") as f:
            protocol = json.load(f)
        return jsonify(protocol), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@protocols_bp.route("/protocols", methods=["POST"])
@cross_origin()
def create_protocol():
    """Create a new interview protocol."""
    try:
        content = request.json
        name = content.get("name")
        protocol = content.get("protocol")
        if not name or not protocol:
            return jsonify({"error": "Missing name or protocol data"}), 400
        safe_name = os.path.basename(name).replace(" ", "_")
        path = os.path.join(_INTERVIEW_DIR, f"{safe_name}.json")
        if os.path.isfile(path):
            return jsonify({"error": "Protocol already exists"}), 409
        with open(path, "w", encoding="utf-8") as f:
            json.dump(protocol, f, indent=2, ensure_ascii=False)
        return jsonify({"status": "created", "name": safe_name}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@protocols_bp.route("/protocols/<name>", methods=["PUT"])
@cross_origin()
def update_protocol(name):
    """Update an existing interview protocol."""
    try:
        safe_name = os.path.basename(name)
        path = os.path.join(_INTERVIEW_DIR, f"{safe_name}.json")
        if not os.path.isfile(path):
            return jsonify({"error": "Protocol not found"}), 404
        protocol = request.json
        with open(path, "w", encoding="utf-8") as f:
            json.dump(protocol, f, indent=2, ensure_ascii=False)
        return jsonify({"status": "updated", "name": safe_name}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@protocols_bp.route("/protocols/<name>", methods=["DELETE"])
@cross_origin()
def delete_protocol(name):
    """Delete an interview protocol."""
    try:
        safe_name = os.path.basename(name)
        if safe_name == "interview_default":
            return jsonify({"error": "Cannot delete the default protocol"}), 403
        path = os.path.join(_INTERVIEW_DIR, f"{safe_name}.json")
        if not os.path.isfile(path):
            return jsonify({"error": "Protocol not found"}), 404
        os.remove(path)
        return jsonify({"status": "deleted", "name": safe_name}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@protocols_bp.route("/protocols/<name>/export", methods=["GET"])
@cross_origin()
def export_protocol(name):
    """Export a protocol as a downloadable JSON file."""
    try:
        safe_name = os.path.basename(name)
        path = os.path.join(_INTERVIEW_DIR, f"{safe_name}.json")
        if not os.path.isfile(path):
            return jsonify({"error": "Protocol not found"}), 404
        return send_from_directory(
            _INTERVIEW_DIR,
            f"{safe_name}.json",
            as_attachment=True,
            download_name=f"{safe_name}.json",
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@protocols_bp.route("/protocols/import", methods=["POST"])
@cross_origin()
def import_protocol():
    """Import a protocol from uploaded JSON."""
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400
        file = request.files["file"]
        name = os.path.splitext(file.filename)[0]
        safe_name = os.path.basename(name).replace(" ", "_")
        protocol = json.load(file)
        path = os.path.join(_INTERVIEW_DIR, f"{safe_name}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(protocol, f, indent=2, ensure_ascii=False)
        return jsonify({"status": "imported", "name": safe_name}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
