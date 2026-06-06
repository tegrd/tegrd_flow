"""Config flow pro TEGRD Flow integraci."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_NAME, CONF_PORT, DEFAULT_PORT, DOMAIN

_LOGGER = logging.getLogger(__name__)


class TegrdFlowConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            port = user_input.get(CONF_PORT, DEFAULT_PORT)

            # Otestuj spojení a získej device serial pro unique_id
            session = async_get_clientsession(self.hass)
            try:
                async with asyncio.timeout(5):
                    async with session.get(f"http://{host}:{port}/info") as resp:
                        if resp.status != 200:
                            errors["base"] = "cannot_connect"
                        else:
                            data = await resp.json(content_type=None)
                            serial = data.get("device")
                            if not serial:
                                errors["base"] = "invalid_response"
                            else:
                                await self.async_set_unique_id(serial)
                                self._abort_if_unique_id_configured()
                                name = user_input.get(CONF_NAME) or serial
                                return self.async_create_entry(
                                    title=name,
                                    data={
                                        CONF_HOST: host,
                                        CONF_PORT: port,
                                        CONF_NAME: name,
                                    },
                                )
            except asyncio.TimeoutError:
                errors["base"] = "timeout"
            except aiohttp.ClientError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Neočekávaná chyba")
                errors["base"] = "unknown"

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
                vol.Optional(CONF_NAME): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
