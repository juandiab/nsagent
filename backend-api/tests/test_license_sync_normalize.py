import pytest

from app.services.license_sync_service import normalize_license_sync_payload, post_license_sync


@pytest.mark.asyncio
async def test_post_license_sync_treats_nested_expired_detail(monkeypatch):
    class FakeResponse:
        status_code = 403
        content = b"{}"

        @staticmethod
        def json():
            return {
                "detail": {
                    "status": "expired",
                    "message": "License expired.",
                    "licenseType": "free",
                    "expirationDate": "2026-06-04T22:50:48.776000Z",
                }
            }

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, url, json):
            return FakeResponse()

    monkeypatch.setattr("app.services.license_sync_service.httpx.AsyncClient", lambda **kwargs: FakeClient())

    result = await post_license_sync(
        app_fingerprint="fp",
        app_name="JPilot",
        license_code="RKOP-BGRM-RSA7-CUBK",
    )
    assert result.is_terminal
    assert result.status == "expired"
    assert result.payload["licenseType"] == "free"
