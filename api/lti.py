"""
LTI 1.0 Provider integration for SRL Agent
Uses OAuth 1.0 (HMAC-SHA1) and maps LTI launch to SRL conversation start.
"""

from flask import Blueprint, request, jsonify
import hashlib
import hmac
import base64
from urllib.parse import quote
import os

from app.core import start_conversation_core

# Blueprint
lti_bp = Blueprint("lti", __name__, url_prefix="/lti")

# LTI credentials (MOVE TO ENV LATER)
LTI_CONSUMER_KEY = os.getenv("LTI_CONSUMER_KEY", "moodle_key")
LTI_SHARED_SECRET = os.getenv("LTI_SHARED_SECRET", "geheimer_schluessel_123")


def create_oauth_base_string(params):
    """Create OAuth 1.0 base string"""
    method = request.method
    url = request.url.split("?")[0]
    sorted_params = sorted(
        [(k, v) for k, v in params.items() if k != "oauth_signature"]
    )
    param_string = "&".join(
        f"{quote(str(k), safe='')}={quote(str(v), safe='')}"
        for k, v in sorted_params
    )
    return f"{method}&{quote(url, safe='')}&{quote(param_string, safe='')}"


def verify_oauth_signature(params, secret):
    """Verify OAuth 1.0 HMAC-SHA1 signature"""
    received_signature = params.get("oauth_signature", "")
    base_string = create_oauth_base_string(params)
    key = quote(secret, safe="") + "&"
    computed_signature = base64.b64encode(
        hmac.new(
            key.encode("utf-8"),
            base_string.encode("utf-8"),
            hashlib.sha1,
        ).digest()
    ).decode("utf-8")

    return hmac.compare_digest(received_signature, computed_signature)


@lti_bp.route("/launch", methods=["POST"])
def lti_launch():
    """
    LTI Launch endpoint
    Called by Moodle / OpenChat via LTI
    """
    params = request.form.to_dict()

    # 1️⃣ Verify consumer key
    if params.get("oauth_consumer_key") != LTI_CONSUMER_KEY:
        return "Invalid LTI consumer key", 401

    # 2️⃣ Verify OAuth signature
    if not verify_oauth_signature(params, LTI_SHARED_SECRET):
        return "Invalid OAuth signature", 401

    # 3️⃣ Extract user & context
    lti_user_id = params.get("user_id")
    context_id = params.get("context_id", "unknown_context")

    if not lti_user_id:
        return "Missing LTI user_id", 400

    # 4️⃣ Map to SRL identifiers
    client = "lti"
    userid = f"{context_id}:{lti_user_id}"

    # Language handling (default: German)
    language = params.get("launch_presentation_locale", "de")[:2]

    # 5️⃣ Start SRL conversation
    message, status = start_conversation_core(
        language=language,
        client=client,
        userid=userid,
    )

    # 6️⃣ Return SRL agent response
    return jsonify(
        {
            "message": message,
            "client": client,
            "userid": userid,
        }
    ), status
