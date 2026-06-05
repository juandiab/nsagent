import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.auth_lockout_service import (
    LOGIN_MAX_FAILURES,
    clear_login_lockout,
    get_login_lockout_message,
    record_login_failure,
)
from app.services.password_reset_service import (
    RECOVERY_CODE_LENGTH,
    RECOVERY_MAX_ATTEMPTS,
    RECOVERY_ATTEMPTS_EXCEEDED_MESSAGE,
    _RECOVERY_CODE_ALPHABET,
    _generate_code,
    _record_recovery_failure,
)


def test_generate_recovery_code_length_and_alphabet():
    code = _generate_code()
    assert len(code) == RECOVERY_CODE_LENGTH
    assert all(char in _RECOVERY_CODE_ALPHABET for char in code)


def test_record_login_failure_locks_after_max_attempts():
    store: dict = {}

    async def find_one(query):
        return store.get(query["username"])

    async def update_one(query, update, upsert=False):
        username = query["username"]
        doc = store.get(username, {"username": username, "failedAttempts": 0})
        doc.update(update["$set"])
        store[username] = doc
        return MagicMock()

    db = MagicMock()
    db.authLoginLockouts.find_one = AsyncMock(side_effect=find_one)
    db.authLoginLockouts.update_one = AsyncMock(side_effect=update_one)
    db.authLoginLockouts.delete_one = AsyncMock()

    for _ in range(LOGIN_MAX_FAILURES - 1):
        message = asyncio.run(record_login_failure(db, username="Admin"))
        assert message is None

    message = asyncio.run(record_login_failure(db, username="admin"))
    assert message is not None
    assert "Too many failed sign-in attempts" in message

    locked_message = asyncio.run(get_login_lockout_message(db, username="admin"))
    assert locked_message == message


def test_clear_login_lockout_removes_record():
    db = MagicMock()
    db.authLoginLockouts.delete_one = AsyncMock()
    asyncio.run(clear_login_lockout(db, username="admin"))
    db.authLoginLockouts.delete_one.assert_awaited_once_with({"username": "admin"})


def test_record_recovery_failure_deletes_code_after_max_attempts():
    doc = {"_id": "code-id", "failedAttempts": RECOVERY_MAX_ATTEMPTS - 1}
    db = MagicMock()
    db.passwordResetCodes.delete_one = AsyncMock()
    db.passwordResetCodes.update_one = AsyncMock()

    with pytest.raises(ValueError, match=RECOVERY_ATTEMPTS_EXCEEDED_MESSAGE):
        asyncio.run(_record_recovery_failure(db, doc))

    db.passwordResetCodes.delete_one.assert_awaited_once_with({"_id": "code-id"})
    db.passwordResetCodes.update_one.assert_not_awaited()


def test_record_recovery_failure_increments_before_max():
    doc = {"_id": "code-id", "failedAttempts": 1}
    db = MagicMock()
    db.passwordResetCodes.delete_one = AsyncMock()
    db.passwordResetCodes.update_one = AsyncMock()

    with pytest.raises(ValueError, match="Invalid or expired recovery code"):
        asyncio.run(_record_recovery_failure(db, doc))

    db.passwordResetCodes.update_one.assert_awaited_once()
    db.passwordResetCodes.delete_one.assert_not_awaited()
