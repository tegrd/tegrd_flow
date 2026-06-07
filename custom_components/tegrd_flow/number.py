"""Number entity pro TEGRD Flow – slidery SSR1/SSR2 (funguje v manuálním režimu)."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL
from .coordinator import TegrdFlowCoordinator


@dataclass(frozen=True)
class TegrdFlowNumberDescription(NumberEntityDescription):
    payload_key: str = ""


NUMBERS: tuple[TegrdFlowNumberDescription, ...] = (
    TegrdFlowNumberDescription(
        key="ssr1_set",
        translation_key="ssr1_set",
        name="SSR 1 výstup",
        icon="mdi:electric-switch",
        native_unit_of_measurement=PERCENTAGE,
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        mode=NumberMode.SLIDER,
        payload_key="ssr1",
    ),
    TegrdFlowNumberDescription(
        key="ssr2_set",
        translation_key="ssr2_set",
        name="SSR 2 výstup",
        icon="mdi:electric-switch",
        native_unit_of_measurement=PERCENTAGE,
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        mode=NumberMode.SLIDER,
        payload_key="ssr2",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: TegrdFlowCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(TegrdFlowNumber(coordinator, desc) for desc in NUMBERS)


class TegrdFlowNumber(CoordinatorEntity[TegrdFlowCoordinator], NumberEntity):
    """Slider pro SSR výstup. Hodnotu lze měnit jen v manuálním režimu."""

    entity_description: TegrdFlowNumberDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: TegrdFlowCoordinator,
        description: TegrdFlowNumberDescription,
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
    def available(self) -> bool:
        # Slider má smysl jen v manuálním režimu
        if not self.coordinator.data:
            return False
        return bool(self.coordinator.data.get("manual"))

    @property
    def native_value(self) -> float | None:
        if not self.coordinator.data:
            return None
        try:
            return float(self.coordinator.data.get(self.entity_description.payload_key, 0))
        except (TypeError, ValueError):
            return None

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_post_control(
            {self.entity_description.payload_key: int(value)}
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()
