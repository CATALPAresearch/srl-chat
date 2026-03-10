from flask import Blueprint, request, Response, redirect
from urllib.parse import quote

lti_bp = Blueprint("lti", __name__, url_prefix="/lti")

@lti_bp.route("/launch", methods=["POST"])
def launch():
    p = request.form.to_dict()
    context_id = p.get('context_id', 'ctx')
    user_id = p.get('user_id', 'user')
    userid = f"{context_id}:{user_id}"
    return redirect(f"/lti/ui?userid={quote(userid)}")

@lti_bp.route("/ui", methods=["GET"])
def lti_ui():
    userid = request.args.get("userid", "lti-anonymous")
    with open("static/lti/index.html", "r", encoding="utf-8") as f:
        html = f.read()
    html = html.replace("__LTI_USERID__", userid)
    return Response(html, mimetype="text/html")