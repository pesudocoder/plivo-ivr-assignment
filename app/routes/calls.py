from flask import current_app, jsonify, render_template, request

from app.config import MissingCredentialsError
from app.plivo_client import InvalidNumberError, PlivoCallError, make_outbound_call
from app.routes import bp
from app.security import local_only


def _error(message, status_code):
    return jsonify(status="error", error=message), status_code


@bp.get("/")
@local_only
def index():
    return render_template("index.html", target_number=current_app.config.get("TARGET_NUMBER") or "")


@bp.post("/call")
@local_only
def call():
    body = request.get_json(silent=True)
    if body is None:
        body = {}
    if not isinstance(body, dict):
        return _error('Request body must be a JSON object, e.g. {"to": "+919876543210"}.', 400)

    try:
        request_uuid = make_outbound_call(current_app.config, to_number=body.get("to"))
    except InvalidNumberError as exc:
        return _error(str(exc), 400)
    except MissingCredentialsError as exc:
        return _error(str(exc), 500)
    except PlivoCallError as exc:
        return _error(str(exc), 502)

    return jsonify(status="initiated", request_uuid=request_uuid)
