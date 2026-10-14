import importlib.util
from pathlib import Path

import pytest

from tests.conftest import TEST_CONFIG

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "make_call.py"


@pytest.fixture
def make_call():
    spec = importlib.util.spec_from_file_location("make_call", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def call_env(monkeypatch):
    for key in ("PLIVO_AUTH_ID", "PLIVO_AUTH_TOKEN", "PLIVO_FROM_NUMBER", "TARGET_NUMBER", "PUBLIC_BASE_URL"):
        monkeypatch.setenv(key, TEST_CONFIG[key])


def test_cli_prints_request_uuid(make_call, call_env, mock_plivo, capsys):
    exit_code = make_call.main([])

    output = capsys.readouterr()
    assert exit_code == 0
    assert "test-request-uuid" in output.out
    assert TEST_CONFIG["PLIVO_AUTH_TOKEN"] not in output.out + output.err
    assert mock_plivo.return_value.calls.create.call_args.kwargs["to_"] == TEST_CONFIG["TARGET_NUMBER"]


def test_r2_cli_to_flag_overrides_target(make_call, call_env, mock_plivo):
    assert make_call.main(["--to", "+919999999999"]) == 0
    assert mock_plivo.return_value.calls.create.call_args.kwargs["to_"] == "+919999999999"


def test_cli_prints_clear_error_when_config_missing(make_call, mock_plivo, capsys):
    exit_code = make_call.main([])

    output = capsys.readouterr()
    assert exit_code == 1
    assert "Error:" in output.err
    assert "PLIVO_AUTH_ID" in output.err
    mock_plivo.assert_not_called()
