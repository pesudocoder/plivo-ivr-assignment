import logging
import xml.etree.ElementTree as ET


def test_r11_answer_returns_valid_plivo_xml(client):
    response = client.post("/answer")

    assert response.status_code == 200
    assert response.mimetype == "application/xml"
    root = ET.fromstring(response.get_data())
    assert root.tag == "Response"
    assert [child.tag for child in root] == ["Speak", "Hangup"]
    assert "Setup is working" in root.find("Speak").text


def test_hangup_returns_200(client, caplog):
    with caplog.at_level(logging.INFO):
        response = client.post(
            "/hangup",
            data={"CallUUID": "uuid-123", "CallStatus": "completed", "HangupCause": "NORMAL_HANGUP"},
        )

    assert response.status_code == 200
    assert "uuid-123" in caplog.text
    assert "completed" in caplog.text
