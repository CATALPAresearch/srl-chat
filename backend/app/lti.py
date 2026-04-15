from flask import Blueprint, request, redirect, session, send_from_directory
import os

_LTI_STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'static', 'lti')

lti_bp = Blueprint("lti", __name__, url_prefix="/lti")

_INSTRUCTOR_ROLES = {
    "instructor", "teacher", "faculty", "staff", "administrator",
    "urn:lti:role:ims/lis/instructor",
    "urn:lti:role:ims/lis/teachingassistant",
    "urn:lti:instrole:ims/lis/instructor",
    "urn:lti:instrole:ims/lis/administrator",
}


def _normalize_role(raw_roles: str) -> str:
    """Map LTI 1.1 roles string to 'teacher' or 'student'."""
    for part in raw_roles.lower().split(","):
        if part.strip() in _INSTRUCTOR_ROLES:
            return "teacher"
    return "student"


@lti_bp.route("/launch", methods=["POST"])
def launch():
    p = request.form.to_dict()
    userid = f"{p.get('context_id')}:{p.get('user_id')}"

    # store LTI context (minimal)
    session["lti_user"] = userid
    session["lti_context"] = p.get("context_id")
    session["lti_role"] = _normalize_role(p.get("roles", ""))

    return redirect("/lti/ui")

@lti_bp.route("/ui", methods=["GET"])
def lti_ui():
    return send_from_directory(_LTI_STATIC_DIR, 'index.html')
