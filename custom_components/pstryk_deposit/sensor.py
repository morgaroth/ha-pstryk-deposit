"""Prosumer deposit sensors."""
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .const import DOMAIN
from .helpers import normalize_description


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


class ProsumerDepositLastTransactionSensor(CoordinatorEntity, SensorEntity):
    """Last deposit transactions."""

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
                normalize_description(transactions[0].get("description") or "")
        return None

    @property
    def extra_state_attributes(self):
        if not self.coordinator.data:
            return None
        transactions = self.coordinator.data.get("transactions", [])
        if not transactions:
            return None
        return {
            "last_10_transactions": [
                {
                    k: (normalize_description(v) if k == "description" and isinstance(v, str) else v)
                    for k, v in t.items()
                    if k not in ("id", "contract")
                }
                for t in transactions[:10]
            ]
        }
