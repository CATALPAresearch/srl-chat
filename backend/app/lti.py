from flask import Blueprint, request, redirect, session, send_from_directory
import os

_LTI_STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'static', 'lti')

lti_bp = Blueprint("lti", __name__, url_prefix="/lti")


@lti_bp.route("/launch", methods=["POST"])
def launch():
    p = request.form.to_dict()
    userid = f"{p.get('context_id')}:{p.get('user_id')}"

    # store LTI context (minimal)
    session["lti_user"] = userid
    session["lti_context"] = p.get("context_id")

    return redirect("/lti/ui")

@lti_bp.route("/ui", methods=["GET"])
def lti_ui():
    return send_from_directory(_LTI_STATIC_DIR, 'index.html')
