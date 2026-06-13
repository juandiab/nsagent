import json

from app.schemas.copilot import ToolCallTrace
from app.services.copilot_deploy import (
    detect_nextgen_application_form_submission,
    format_create_application_response,
    parse_backend_servers,
    parse_configuration_form_fields,
)
from app.services.copilot_orchestration import deployment_write_complete
from app.services.copilot_orchestrator import _deployment_may_be_incomplete


_FORM = """Configuration inputs for: Create IIS Load Balancer
- Application Name: iis_lb_app
- Virtual IP (VIP): 192.168.20.227
- Port: 80
- Protocol: HTTP
- Backend IIS Server IPs: 192.168.21.227, 192.168.21.228, 192.168.21.229
- Load Balancing Method: LEASTCONNECTION

Proceed with the configuration on the connected appliance using these values."""

_STOREFRONT_FORM = """Configuration inputs for: StoreFront Load Balancer Configuration
- Application Name: storefront_lb
- VIP Address: 192.168.21.230
- Protocol: SSL_BRIDGE
- VIP Port: 443
- Backend StoreFront Server IPs (comma-separated): 192.168.21.231, 192.168.21.232
- Backend Server Port: 443
- Load Balancing Algorithm: LEASTCONNECTION

Proceed with the configuration on the connected appliance using these values."""


def test_parse_nextgen_form_fields():
    fields = parse_configuration_form_fields(_FORM)
    assert fields["name"] == "iis_lb_app"
    assert fields["virtual_ip"] == "192.168.20.227"
    assert fields["port"] == "80"
    assert fields["protocol"] == "HTTP"
    assert "192.168.21.227" in fields["servers"]


def test_parse_backend_servers():
    assert parse_backend_servers("10.0.0.1, 10.0.0.2") == ["10.0.0.1", "10.0.0.2"]


def test_detect_nextgen_application_form_submission():
    assert detect_nextgen_application_form_submission(_FORM) is True
    assert detect_nextgen_application_form_submission(_STOREFRONT_FORM) is True


def test_parse_storefront_form_fields():
    fields = parse_configuration_form_fields(_STOREFRONT_FORM)
    assert fields["name"] == "storefront_lb"
    assert fields["virtual_ip"] == "192.168.21.230"
    assert fields["port"] == "443"
    assert fields["servers_port"] == "443"
    assert fields["protocol"] == "SSL_BRIDGE"
    assert "192.168.21.231" in fields["servers"]


def test_classic_lb_form_submission_not_nextgen():
    classic = """Configuration inputs for: Load balancer — Application
- Virtual server name: lb_app_01
- VIP address: 10.0.0.10
- Backend IP addresses (comma-separated): 10.0.0.1
"""
    assert detect_nextgen_application_form_submission(classic) is False


def test_format_create_application_response():
    text = format_create_application_response(
        "Martica",
        {
            "application": {
                "name": "iis_lb_app",
                "virtual_ip": "192.168.20.227",
                "port": 80,
                "protocol": "HTTP",
                "servers": ["192.168.21.227"],
            }
        },
    )
    assert "created via Next-Gen API" in text
    assert "iis_lb_app" in text


def test_nextgen_create_marks_deployment_complete():
    traces = [
        ToolCallTrace(
            name="netscaler_create_application",
            arguments={"name": "iis_lb_app"},
            result=json.dumps({"success": True, "application": {"name": "iis_lb_app"}}),
        )
    ]
    assert deployment_write_complete(traces) is True
    assert _deployment_may_be_incomplete(traces, _FORM, "operator") is False
