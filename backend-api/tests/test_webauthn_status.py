from app.routers.webauthn import _build_status_response


def test_status_disabled():
    response = _build_status_response(
        username="alice",
        exists=True,
        has_passkey=True,
        passkey_policy="disabled",
        can_register=True,
    )
    assert response.passkeyRequired is False
    assert response.canRegister is False
    assert response.passkeyRecommended is False
    assert response.passkeyEnforced is False


def test_status_enabled_without_passkey():
    response = _build_status_response(
        username="alice",
        exists=True,
        has_passkey=False,
        passkey_policy="enabled",
        can_register=True,
    )
    assert response.passkeyRequired is False
    assert response.passkeyRecommended is True
    assert response.canRegister is True


def test_status_enabled_with_passkey():
    response = _build_status_response(
        username="alice",
        exists=True,
        has_passkey=True,
        passkey_policy="enabled",
        can_register=True,
    )
    assert response.passkeyRequired is True
    assert response.passkeyRecommended is False


def test_status_enforced_without_passkey():
    response = _build_status_response(
        username="alice",
        exists=True,
        has_passkey=False,
        passkey_policy="enforced",
        can_register=True,
    )
    assert response.passkeyRequired is False
    assert response.passkeyEnforced is True
    assert response.passkeyRecommended is True


def test_status_enforced_with_passkey():
    response = _build_status_response(
        username="alice",
        exists=True,
        has_passkey=True,
        passkey_policy="enforced",
        can_register=True,
    )
    assert response.passkeyRequired is True
    assert response.passkeyEnforced is True
