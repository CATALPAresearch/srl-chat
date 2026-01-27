from flask import Blueprint, request, Response

lti_bp = Blueprint("lti", __name__, url_prefix="/lti")



from flask import redirect, session

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
    return Response(
        open("static/lti/index.html").read(),
        mimetype="text/html"
    )
