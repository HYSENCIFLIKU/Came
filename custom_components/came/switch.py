"""Switch platform for the Came Eti Domo integration."""
from __future__ import annotations
import logging
from typing import Any
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import slugify
from .const import DOMAIN
from .coordinator import CameCoordinator
from .entity import CameEntity
_LOGGER=logging.getLogger(__name__)
async def async_setup_entry(hass:HomeAssistant,config_entry:ConfigEntry,async_add_entities:AddEntitiesCallback)->None:
    coordinator:CameCoordinator=hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities(Relay(coordinator,item) for item in coordinator.data.get("relays",{}).values())
class Relay(CameEntity,SwitchEntity):
    def __init__(self,coordinator:CameCoordinator,item:dict)->None:
        super().__init__(coordinator,"relays",item["act_id"])
        object_id=item["name"].lower().replace(" ","_")+"_"+str(item["act_id"])
        self.entity_id="switch."+slugify(object_id); self._attr_unique_id="switch."+object_id; self._attr_name=item["name"]
    @property
    def is_on(self)->bool:
        item=self._item
        return bool(item and item.get("status"))
    async def async_turn_on(self,**kwargs:Any)->None:
        self._optimistic_update(status=1)
        try: await self.hass.async_add_executor_job(self.coordinator.hub.switch,self._id,True,False)
        except Exception: _LOGGER.exception("Failed to turn on CAME relay %s",self._id); raise
    async def async_turn_off(self,**kwargs:Any)->None:
        self._optimistic_update(status=0)
        try: await self.hass.async_add_executor_job(self.coordinator.hub.switch,self._id,False,False)
        except Exception: _LOGGER.exception("Failed to turn off CAME relay %s",self._id); raise
