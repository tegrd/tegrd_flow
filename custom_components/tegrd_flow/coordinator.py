"""Data update coordinator for TEGRD Flow."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_HOST,
    CONF_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class TegrdFlowCoordinator(DataUpdateCoordinator):
    """Polling coordinator pro lokální TEGRD Flow zařízení."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.host: str = entry.data[CONF_HOST]
        self.port: int = entry.data.get(CONF_PORT, 5102)
        self.entry = entry
        self._session = async_get_clientsession(hass)

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{self.host}",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    async def _async_update_data(self) -> dict:
        """Stáhne /info z lokálního zařízení."""
        try:
            async with asyncio.timeout(5):
                async with self._session.get(f"{self.base_url}/info") as resp:
                    if resp.status != 200:
                        raise UpdateFailed(f"HTTP {resp.status}")
                    return await resp.json(content_type=None)
        except (asyncio.TimeoutError, aiohttp.ClientError) as err:
            raise UpdateFailed(f"Chyba komunikace: {err}") from err

    @property
    def device_serial(self) -> str:
        if self.data:
            return self.data.get("device", self.host)
        return self.host

    @property
    def fw_version(self) -> str:
        return self.data.get("fw_version", "?") if self.data else "?"

    async def async_post_control(self, payload: dict) -> bool:
        """Pošle POST /control se změnami (manual, allow_flows, ssr1, ssr2)."""
        try:
            async with asyncio.timeout(5):
                async with self._session.post(
                    f"{self.base_url}/control", json=payload
                ) as resp:
                    if resp.status != 200:
                        _LOGGER.warning("Control POST HTTP %s", resp.status)
                        return False
                    # Server vrátí aktualizované /info – rovnou ho použij
                    self.async_set_updated_data(await resp.json(content_type=None))
                    return True
        except (asyncio.TimeoutError, aiohttp.ClientError) as err:
            _LOGGER.warning("Control POST selhal: %s", err)
            return False
