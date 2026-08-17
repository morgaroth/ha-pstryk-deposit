"""Prosumer deposit sensors."""
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        ProsumerDepositSensor(coordinator, entry),
        ProsumerDepositLastTransactionSensor(coordinator, entry),
    ])


class ProsumerDepositSensor(CoordinatorEntity, SensorEntity):
    """Current prosumer deposit balance."""

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_native_unit_of_measurement = "PLN"
    _attr_icon = "mdi:piggy-bank-outline"

    def __init__(self, coordinator: DataUpdateCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_prosumer_deposit"
        self._attr_name = "Pstryk Depozyt Prosumencki"

    @property
    def native_value(self):
        if self.coordinator.data:
            return self.coordinator.data.get("prosumer_deposit")
        return None

    @property
    def extra_state_attributes(self):
        if not self.coordinator.data:
            return None
        attrs = {}
        by_meter = self.coordinator.data.get("prosumer_deposit_by_meter")
        if by_meter:
            attrs["deposit_by_meter"] = by_meter
        transactions = self.coordinator.data.get("transactions", [])
        attrs["transaction_count"] = len(transactions)
        return attrs


class ProsumerDepositLastTransactionSensor(CoordinatorEntity, SensorEntity):
    """Last deposit transaction amount."""

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "PLN"
    _attr_icon = "mdi:bank-transfer"

    def __init__(self, coordinator: DataUpdateCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_last_deposit_transaction"
        self._attr_name = "Pstryk Ostatnia Transakcja Depozytu"

    @property
    def native_value(self):
        if self.coordinator.data:
            transactions = self.coordinator.data.get("transactions", [])
            if transactions:
                return transactions[0].get("amount")
        return None

    @property
    def extra_state_attributes(self):
        if not self.coordinator.data:
            return None
        transactions = self.coordinator.data.get("transactions", [])
        if not transactions:
            return None
        last = transactions[0]
        return {
            "description": last.get("description"),
            "timestamp": last.get("timestamp"),
            "contract": last.get("contract"),
            "id": last.get("id"),
        }
