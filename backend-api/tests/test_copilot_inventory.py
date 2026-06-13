import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.copilot_inventory import (  # noqa: E402
    detect_ip_inventory_request,
    format_ip_inventory_response,
    user_asks_for_all_ips,
)


def test_detect_ip_inventory_request():
    assert detect_ip_inventory_request(
        "List all IP addresses on the connected appliance with their types (NSIP, SNIP, VIP, etc.)."
    )
    assert detect_ip_inventory_request("show ns ip")
    assert not detect_ip_inventory_request(
        "show me all the network information about routes, vlans and IPs"
    )
    assert not detect_ip_inventory_request("show me the vlans")
    assert not detect_ip_inventory_request("Add a new SNIP on VLAN 100")
    assert not detect_ip_inventory_request("What is the management IP?")
    assert not detect_ip_inventory_request(
        "Configuration inputs for: StoreFront Load Balancer Configuration\n"
        "- Application Name: storefront_lb\n"
        "- VIP Address: 192.168.21.230\n"
        "- Backend StoreFront Server IPs (comma-separated): 192.168.21.231\n"
    )


def test_user_asks_for_all_ips():
    assert user_asks_for_all_ips("list every ip on the box")
    assert user_asks_for_all_ips("show snip configuration")


def test_format_ip_inventory_response():
    text = format_ip_inventory_response(
        "Martica",
        {
            "managementIp": "192.168.20.220",
            "ipCount": 4,
            "addresses": [{"ipAddress": "192.168.20.220", "type": "NSIP"}],
        },
    )
    assert "Martica" in text
    assert "4 IP address(es)" in text
    assert "192.168.20.220" in text
    assert "| IP Address |" not in text
