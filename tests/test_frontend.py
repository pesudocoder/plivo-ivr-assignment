import re

import pytest

from tests.conftest import TEST_CONFIG

TUNNEL_HEADERS = {"X-Forwarded-For": "203.0.113.7"}


def test_r15_index_page_renders(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.mimetype == "text/html"
    html = response.get_data(as_text=True)
    assert "<title>InspireWorks IVR Demo</title>" in html
    assert re.search(r"<button[^>]*>Start Call</button>", html)
    assert "How to test" in html
    assert "E.164" in html


def test_r15_index_prefills_target_number(client):
    html = client.get("/").get_data(as_text=True)

    field = re.search(r'<input id="to"[^>]*>', html).group(0)
    assert f'value="{TEST_CONFIG["TARGET_NUMBER"]}"' in field


def test_r15_index_prefill_is_escaped(app, client):
    app.config["TARGET_NUMBER"] = '"><script>alert(1)</script>'

    html = client.get("/").get_data(as_text=True)

    assert "<script>alert(1)</script>" not in html


def test_r15_index_has_no_secrets(app, client):
    html = client.get("/").get_data(as_text=True)

    assert app.config["BIRTHDATE_OTP"] not in html
    assert app.config["PLIVO_AUTH_ID"] not in html
    assert app.config["PLIVO_AUTH_TOKEN"] not in html


def test_r15_index_posts_to_call_endpoint(client):
    html = client.get("/").get_data(as_text=True)

    assert re.search(r'fetch\(\s*"/call"\s*,\s*\{\s*method:\s*"POST"', html)
    assert "JSON.stringify({ to:" in html
    assert "button.disabled = true" in html
    assert "request_uuid" in html and "data.error" in html


def test_r15_index_has_no_external_dependencies(client):
    html = client.get("/").get_data(as_text=True)

    assert not re.search(r'<(script|link|img)[^>]+(src|href)="(https?:)?//', html)


@pytest.mark.parametrize("method,path", [("get", "/"), ("post", "/call")])
def test_call_trigger_blocked_via_tunnel(client, mock_plivo, method, path):
    response = getattr(client, method)(path, headers=TUNNEL_HEADERS)

    assert response.status_code == 403
    assert "only available from this machine" in response.get_json()["error"]
    mock_plivo.assert_not_called()


@pytest.mark.parametrize("method,path", [("get", "/"), ("post", "/call")])
def test_call_trigger_blocked_from_non_loopback_address(client, mock_plivo, method, path):
    response = getattr(client, method)(path, environ_base={"REMOTE_ADDR": "192.168.1.50"})

    assert response.status_code == 403
    mock_plivo.assert_not_called()


def test_call_trigger_blocked_from_cross_site_origin(client, mock_plivo):
    response = client.post("/call", headers={"Origin": "https://evil.example"})

    assert response.status_code == 403
    mock_plivo.assert_not_called()


def test_call_trigger_allows_same_origin_browser_request(client, mock_plivo):
    response = client.post("/call", json={}, headers={"Origin": "http://localhost"})

    assert response.status_code == 200
    mock_plivo.return_value.calls.create.assert_called_once()


@pytest.mark.parametrize(
    "path",
    ["/answer", "/otp/verify", "/menu/language", "/menu/language/select", "/menu/action",
     "/menu/action/select", "/menu/dial/status", "/hangup"],
)
def test_webhooks_still_public_via_tunnel(client, path):
    response = client.post(path, data={"CallUUID": "call-uuid-x"}, headers=TUNNEL_HEADERS)

    assert response.status_code == 200
