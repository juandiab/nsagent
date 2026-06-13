import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.copilot_service_status import (  # noqa: E402
    detect_service_status_request,
    format_service_status_response,
)


def test_detect_service_status_request():
    assert detect_service_status_request("show me the status of the services that are down")
    assert detect_service_status_request("which backends are unhealthy")
    assert not detect_service_status_request("show me the vlans")
    assert not detect_service_status_request("list all IP addresses")


def test_format_service_status_response():
    text = format_service_status_response(
        "Martica",
        {
            "downCount": 1,
            "services": [
                {
                    "name": "dns_srv_2",
                    "ipAddress": "1.2.3.4",
                    "port": 53,
                    "state": "DOWN",
                    "boundTo": ["dns_lb_vs"],
                }
            ],
            "serviceGroups": [],
        },
    )
    assert "dns_srv_2" in text
    assert "1.2.3.4" in text
