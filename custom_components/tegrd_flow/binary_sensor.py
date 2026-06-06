"""Binary senzory pro TEGRD Flow."""
from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL
from .coordinator import TegrdFlowCoordinator


@dataclass(frozen=True)
class TegrdFlowBinarySensorDescription(BinarySensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], bool] | None = None


BINARY_SENSORS: tuple[TegrdFlowBinarySensorDescription, ...] = (
    TegrdFlowBinarySensorDescription(
        key="allow_flows",
        translation_key="allow_flows",
        name="Regulace přetoků",
        icon="mdi:transmission-tower",
        value_fn=lambda d: bool(d.get("allow_flows")),
    ),
    TegrdFlowBinarySensorDescription(
        key="manual",
        translation_key="manual",
        name="Manuální režim",
        icon="mdi:hand-back-right",
        value_fn=lambda d: bool(d.get("manual")),
    ),
    TegrdFlowBinarySensorDescription(
        key="schedule_active",
        translation_key="schedule_active",
        name="Harmonogram aktivní",
        icon="mdi:calendar-clock",
        value_fn=lambda d: bool(d.get("schedule_active")),
    ),
    TegrdFlowBinarySensorDescription(
        key="spot_enabled",
        translation_key="spot_enabled",
        name="Spot ceny",
        icon="mdi:currency-eur",
        value_fn=lambda d: bool(d.get("spot_enabled")),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: TegrdFlowCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        TegrdFlowBinarySensor(coordinator, desc) for desc in BINARY_SENSORS
    )


class TegrdFlowBinarySensor(CoordinatorEntity[TegrdFlowCoordinator], BinarySensorEntity):
    entity_description: TegrdFlowBinarySensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: TegrdFlowCoordinator,
        description: TegrdFlowBinarySensorDescription,
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
        if not self.coordinator.data or not self.entity_description.value_fn:
            return None
        try:
            return self.entity_description.value_fn(self.coordinator.data)
        except (TypeError, ValueError, KeyError):
            return None

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()
