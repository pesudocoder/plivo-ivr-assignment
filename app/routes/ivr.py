from flask import Response, current_app, request
from plivo import plivoxml

from app.routes import bp


def xml_response(element):
    return Response(element.to_string(False), mimetype="application/xml")


@bp.post("/answer")
def answer():
    # TEMPORARY placeholder for Phase 2; Phase 3 replaces this with the OTP flow.
    response = plivoxml.ResponseElement()
    response.add(plivoxml.SpeakElement("Hello from the Plivo IVR demo. Setup is working."))
    response.add(plivoxml.HangupElement())
    return xml_response(response)


@bp.post("/hangup")
def hangup():
    current_app.logger.info(
        "Call ended: uuid=%s status=%s cause=%s",
        request.form.get("CallUUID"),
        request.form.get("CallStatus"),
        request.form.get("HangupCause"),
    )
    return "", 200
