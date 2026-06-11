import pytest

from app.services.jpilot_settings_service import (
    default_document,
    get_display_home_page,
    get_portal_config,
    update_jpilot_settings,
)
from app.schemas.jpilot_settings import JpilotSettingsUpdate


class FakeCollection:
    def __init__(self):
        self.document = None

    async def find_one(self, query):
        if self.document and self.document.get("_id") == query.get("_id"):
            return self.document
        return None

    async def insert_one(self, document):
        self.document = dict(document)

    async def update_one(self, query, update, upsert=False):
        if self.document is None and upsert:
            self.document = {"_id": query["_id"]}
        if self.document:
            self.document.update(update.get("$set", {}))


class FakeDb:
    def __init__(self):
        self.jpilotSettings = FakeCollection()


@pytest.mark.asyncio
async def test_default_display_home_page_is_enabled():
    db = FakeDb()
    assert await get_display_home_page(db) is True
    config = await get_portal_config(db)
    assert config.displayHomePage is True


@pytest.mark.asyncio
async def test_update_display_home_page_persists():
    db = FakeDb()
    await update_jpilot_settings(db, JpilotSettingsUpdate(displayHomePage=False))
    assert await get_display_home_page(db) is False


def test_default_document_enables_home_page():
    assert default_document()["displayHomePage"] is True
