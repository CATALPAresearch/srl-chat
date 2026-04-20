"""User-info routes: language, role."""
from flask import Blueprint, request, session
from flask_cors import cross_origin

from ..database.crud import get_user, get_language_by_id

user_bp = Blueprint('user', __name__)


@user_bp.route("/user_language/", methods=["GET"])
@cross_origin()
def get_user_language():
    """
    Query params:
        "client": client identifier
        "userid": user ID
    """
    userid = request.args.get('userid')
    client = request.args.get('client')
    user = get_user(userid, client)
    if user:
        user_lang = get_language_by_id(user.language_id)
        return (user_lang.lang_code if user_lang else 'de'), 200
    return 'de', 200  # Default to German for new / standalone users


@user_bp.route("/user_role/", methods=["GET"])
@cross_origin()
def get_user_role():
    """
    Return the role ('student' or 'teacher') for the requesting user.
    Priority: LTI session role → default 'student'.
    Query params: userid, client (reserved for future DB lookup).
    """
    role = session.get("lti_role", "student")
    return role, 200
