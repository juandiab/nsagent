"""Vendor-isolated documentation domains for web search."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.vendor_doc_domains import (  # noqa: E402
    CISCO_DOC_DOMAINS,
    F5_DOC_DOMAINS,
    NETSCALER_DOC_DOMAINS,
    locked_domains_for_vendor,
)


def test_locked_domains_per_vendor():
    assert "cisco.com" in locked_domains_for_vendor("cisco")
    assert "clouddocs.f5.com" in locked_domains_for_vendor("f5")
    assert "docs.citrix.com" in locked_domains_for_vendor("netscaler")
    assert "docs.citrix.com" in locked_domains_for_vendor("sdx")


def test_vendor_domains_do_not_cross():
    assert not any(d in NETSCALER_DOC_DOMAINS for d in CISCO_DOC_DOMAINS)
    assert not any(d in CISCO_DOC_DOMAINS for d in F5_DOC_DOMAINS)
    assert not any(d in F5_DOC_DOMAINS for d in NETSCALER_DOC_DOMAINS)
