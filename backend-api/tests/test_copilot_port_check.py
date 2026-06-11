import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.copilot_port_check import (  # noqa: E402
    detect_appliance_internet_check,
    format_internet_check_response,
)


def test_detect_appliance_internet_check():
    assert detect_appliance_internet_check("does the netscaler have internet access?")
    assert detect_appliance_internet_check("Does Martica have outbound internet connectivity?")
    assert not detect_appliance_internet_check("can you reach the documentation site?")
    assert not detect_appliance_internet_check("show version")


def test_format_internet_check_response():
    text = format_internet_check_response(
        "Martica",
        route_summary="0.0.0.0/0 -> 192.168.20.1",
        ping_summary="4/4 packets received, 0% loss",
        has_default_route=True,
        ping_ok=True,
    )
    assert "Internet access" in text
    assert "Martica" in text
    assert "0.0.0.0/0" in text
