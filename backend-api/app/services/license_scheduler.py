from __future__ import annotations

import asyncio
import logging

from app.config import settings
from app.database import get_database
from app.services.license_service import run_scheduled_license_sync

logger = logging.getLogger(__name__)


async def run_startup_license_sync() -> None:
    """POST /licensing/sync once when the API starts."""
    db = get_database()
    await run_scheduled_license_sync(db)


async def periodic_license_sync(stop_event: asyncio.Event) -> None:
    """Daily POST /licensing/sync (first run happens on startup via ``run_startup_license_sync``)."""
    interval = max(3600, int(settings.license_sync_interval_seconds))
    while not stop_event.is_set():
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval)
        except asyncio.TimeoutError:
            pass
        if stop_event.is_set():
            break
        try:
            db = get_database()
            await run_scheduled_license_sync(db)
        except Exception:
            logger.exception("Daily license sync failed")
