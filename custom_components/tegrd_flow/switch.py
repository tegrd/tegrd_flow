"""Switch entity pro TEGRD Flow – manuální režim a regulace přetoků."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL
from .coordinator import TegrdFlowCoordinator


@dataclass(frozen=True)
class TegrdFlowSwitchDescription(SwitchEntityDescription):
    """Popis switche – mapuje pole z /info na payload pro /control."""

    payload_key: str = ""


SWITCHES: tuple[TegrdFlowSwitchDescription, ...] = (
    TegrdFlowSwitchDescription(
        key="manual",
        translation_key="manual",
        name="Manuální režim",
        icon="mdi:hand-back-right",
        payload_key="manual",
    ),
    TegrdFlowSwitchDescription(
        key="allow_flows",
        translation_key="allow_flows",
        name="Regulace přetoků",
        icon="mdi:transmission-tower",
        payload_key="allow_flows",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: TegrdFlowCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(TegrdFlowSwitch(coordinator, desc) for desc in SWITCHES)


class TegrdFlowSwitch(CoordinatorEntity[TegrdFlowCoordinator], SwitchEntity):
    """Switch ovládající TEGRD Flow přes POST /control."""

    entity_description: TegrdFlowSwitchDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: TegrdFlowCoordinator,
        description: TegrdFlowSwitchDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.device_serial}_{description.key}"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.device_serial)},
            name=self.coordinator.entry.data.get("name", self.coordinator.device_serial),
            manufacturer=MANUFACTURER,
            model=MODEL,
            sw_version=self.coordinator.fw_version,
        )

    @property
    def is_on(self) -> bool | None:
        if not self.coordinator.data:
            return None
        return bool(self.coordinator.data.get(self.entity_description.payload_key))

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_post_control(
            {self.entity_description.payload_key: True}
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_post_control(
            {self.entity_description.payload_key: False}
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()
