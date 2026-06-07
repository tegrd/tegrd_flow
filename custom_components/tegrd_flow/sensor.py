"""Senzory pro TEGRD Flow."""
from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfPower,
)


def _format_uptime(seconds: int) -> str:
    """Formátuje uptime na čitelný string – auto přepíná mezi h/d."""
    s = int(seconds or 0)
    days = s // 86400
    hours = (s % 86400) // 3600
    minutes = (s % 3600) // 60
    if days > 0:
        return f"{days} d {hours} h"
    return f"{hours} h {minutes} min"
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL
from .coordinator import TegrdFlowCoordinator


@dataclass(frozen=True)
class TegrdFlowSensorDescription(SensorEntityDescription):
    """Popis senzoru s vlastní funkcí pro extrakci hodnoty."""

    value_fn: Callable[[dict[str, Any]], Any] | None = None


SENSORS: tuple[TegrdFlowSensorDescription, ...] = (
    TegrdFlowSensorDescription(
        key="ssr1",
        translation_key="ssr1",
        name="SSR 1",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:electric-switch",
        value_fn=lambda d: round(float(d.get("ssr1", 0)), 1),
    ),
    TegrdFlowSensorDescription(
        key="ssr2",
        translation_key="ssr2",
        name="SSR 2",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:electric-switch",
        value_fn=lambda d: round(float(d.get("ssr2", 0)), 1),
    ),
    TegrdFlowSensorDescription(
        key="overflow_sum",
        translation_key="overflow_sum",
        name="Přetoky (průměr)",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: round(float(d.get("overflow_sum", 0)), 0),
    ),
    TegrdFlowSensorDescription(
        key="overflow_tmp",
        translation_key="overflow_tmp",
        name="Přetoky (aktuální)",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: round(float(d.get("overflow_tmp", 0)), 0),
    ),
    TegrdFlowSensorDescription(
        key="ssr1_maxflow",
        translation_key="ssr1_maxflow",
        name="SSR 1 max výkon",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: round(float(d.get("ssr1_maxflow", 0)), 0),
    ),
    TegrdFlowSensorDescription(
        key="ssr2_maxflow",
        translation_key="ssr2_maxflow",
        name="SSR 2 max výkon",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: round(float(d.get("ssr2_maxflow", 0)), 0),
    ),
    TegrdFlowSensorDescription(
        key="rssi",
        translation_key="rssi",
        name="WiFi signál",
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=lambda d: int(d.get("rssi", 0)),
    ),
    TegrdFlowSensorDescription(
        key="runtime",
        translation_key="runtime",
        name="Doba běhu",
        icon="mdi:timer-outline",
        value_fn=lambda d: _format_uptime(d.get("runtime", 0)),
    ),
    TegrdFlowSensorDescription(
        key="fw_version",
        translation_key="fw_version",
        name="Firmware",
        icon="mdi:chip",
        entity_registry_enabled_default=False,
        value_fn=lambda d: d.get("fw_version"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor platform."""
    coordinator: TegrdFlowCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        TegrdFlowSensor(coordinator, desc) for desc in SENSORS
    )


class TegrdFlowSensor(CoordinatorEntity[TegrdFlowCoordinator], SensorEntity):
    """Senzor pro TEGRD Flow zařízení."""

    entity_description: TegrdFlowSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: TegrdFlowCoordinator,
        description: TegrdFlowSensorDescription,
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
            configuration_url=f"{self.coordinator.base_url}/info",
        )

    @property
    def native_value(self) -> Any:
        if not self.coordinator.data or not self.entity_description.value_fn:
            return None
        try:
            return self.entity_description.value_fn(self.coordinator.data)
        except (TypeError, ValueError, KeyError):
            return None

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()
