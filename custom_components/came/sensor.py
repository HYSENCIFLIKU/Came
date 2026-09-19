"""Sensor (analog inputs) platform for the Came Eti Domo integration."""
from __future__ import annotations
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import slugify
from .const import DOMAIN
from .coordinator import CameCoordinator
from .entity import CameEntity
_UNIT_TO_DEVICE_CLASS={"%":SensorDeviceClass.HUMIDITY,"°C":SensorDeviceClass.TEMPERATURE,"C":SensorDeviceClass.TEMPERATURE}
async def async_setup_entry(hass:HomeAssistant,config_entry:ConfigEntry,async_add_entities:AddEntitiesCallback)->None:
    coordinator:CameCoordinator=hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities(CameAnalogSensor(coordinator,item) for item in coordinator.data.get("analogin",{}).values())
class CameAnalogSensor(CameEntity,SensorEntity):
    _attr_state_class=SensorStateClass.MEASUREMENT
    def __init__(self,coordinator:CameCoordinator,item:dict)->None:
        super().__init__(coordinator,"analogin",item["act_id"])
        object_id=item["name"].lower().replace(" ","_")+"_"+str(item["act_id"])
        self.entity_id="sensor."+slugify(object_id); self._attr_unique_id="sensor."+object_id; self._attr_name=item["name"]
        unit=item.get("unit"); self._attr_native_unit_of_measurement=unit; self._attr_device_class=_UNIT_TO_DEVICE_CLASS.get(unit)
    @property
    def native_value(self):
        item=self._item
        return None if item is None else item.get("value")
