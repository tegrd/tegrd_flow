"""Config flow pro TEGRD Flow integraci."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp
import voluptuous as vol

# ZeroconfServiceInfo se přesunul mezi verzemi HA – kompatibilní import
try:
    from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo
except ImportError:  # HA < 2024.4
    from homeassistant.components.zeroconf import ZeroconfServiceInfo  # type: ignore

# ConfigFlowResult byl přidán v 2024.1, fallback na FlowResult
try:
    from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
except ImportError:  # HA < 2024.1
    from homeassistant.config_entries import ConfigFlow  # type: ignore
    from homeassistant.data_entry_flow import FlowResult as ConfigFlowResult  # type: ignore

from homeassistant.const import CONF_HOST
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_NAME, CONF_PORT, DEFAULT_PORT, DOMAIN

_LOGGER = logging.getLogger(__name__)


class TegrdFlowConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow s podporou manuálního zadání i mDNS autodiscovery."""

    VERSION = 1

    def __init__(self) -> None:
        self._discovered_host: str | None = None
        self._discovered_port: int = DEFAULT_PORT
        self._discovered_serial: str | None = None

    async def _fetch_device(self, host: str, port: int) -> dict | None:
        """Stáhne /info ze zařízení."""
        session = async_get_clientsession(self.hass)
        try:
            async with asyncio.timeout(5):
                async with session.get(f"http://{host}:{port}/info") as resp:
                    if resp.status != 200:
                        return None
                    return await resp.json(content_type=None)
        except (asyncio.TimeoutError, aiohttp.ClientError):
            return None

    # ── Manuální zadání IP ────────────────────────────────────────────────────
    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            port = user_input.get(CONF_PORT, DEFAULT_PORT)

            data = await self._fetch_device(host, port)
            if data is None:
                errors["base"] = "cannot_connect"
            else:
                serial = data.get("device")
                if not serial:
                    errors["base"] = "invalid_response"
                else:
                    await self.async_set_unique_id(serial)
                    self._abort_if_unique_id_configured()
                    name = user_input.get(CONF_NAME) or serial
                    return self.async_create_entry(
                        title=name,
                        data={CONF_HOST: host, CONF_PORT: port, CONF_NAME: name},
                    )

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
                vol.Optional(CONF_NAME): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    # ── mDNS autodiscovery ────────────────────────────────────────────────────
    async def async_step_zeroconf(self, discovery_info: ZeroconfServiceInfo) -> ConfigFlowResult:
        """Zachytí oznámení _tegrd-flow._tcp.local."""
        host = discovery_info.host
        port = discovery_info.port or DEFAULT_PORT
        serial = discovery_info.properties.get("device")

        # Pokud TXT záznam neobsahuje device, dotáhni přes HTTP
        if not serial:
            data = await self._fetch_device(host, port)
            if data is None:
                return self.async_abort(reason="cannot_connect")
            serial = data.get("device")
            if not serial:
                return self.async_abort(reason="invalid_response")

        await self.async_set_unique_id(serial)
        self._abort_if_unique_id_configured(updates={CONF_HOST: host})

        self._discovered_host = host
        self._discovered_port = port
        self._discovered_serial = serial

        self.context["title_placeholders"] = {"name": serial}
        return await self.async_step_zeroconf_confirm()

    async def async_step_zeroconf_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Potvrzení přidání nalezeného zařízení."""
        if user_input is not None:
            name = user_input.get(CONF_NAME) or self._discovered_serial
            return self.async_create_entry(
                title=name,
                data={
                    CONF_HOST: self._discovered_host,
                    CONF_PORT: self._discovered_port,
                    CONF_NAME: name,
                },
            )

        schema = vol.Schema({vol.Optional(CONF_NAME, default=self._discovered_serial or ""): str})
        return self.async_show_form(
            step_id="zeroconf_confirm",
            data_schema=schema,
            description_placeholders={
                "name": self._discovered_serial or "?",
                "host": self._discovered_host or "?",
            },
        )
