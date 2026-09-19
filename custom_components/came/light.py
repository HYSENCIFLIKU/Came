"""Light platform for the Came Eti Domo integration."""
from __future__ import annotations
import logging
from typing import Any
from homeassistant.components.light import ColorMode, LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import slugify
from .const import DOMAIN
from .coordinator import CameCoordinator
from .entity import CameEntity
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: CameCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities(CameLight(coordinator, item) for item in coordinator.data.get("lights", {}).values())

class CameLight(CameEntity, LightEntity):
    _attr_color_mode = ColorMode.ONOFF
    _attr_supported_color_modes = {ColorMode.ONOFF}
    def __init__(self, coordinator: CameCoordinator, item: dict) -> None:
        super().__init__(coordinator, "lights", item["act_id"])
        floor_name=item.get("floor_name","")
        object_id=floor_name.lower().replace(" ","_")+"_"+item["name"].lower().replace(" ","_").replace(".","")+"_"+str(item["act_id"])
        self.entity_id="light."+slugify(object_id); self._attr_unique_id="light."+object_id; self._attr_name=item["name"]
    @property
    def is_on(self)->bool:
        item=self._item
        return bool(item and item.get("status"))
    async def async_turn_on(self, **kwargs: Any)->None:
        self._optimistic_update(status=1)
        try: await self.hass.async_add_executor_job(self.coordinator.hub.switch,self._id,True,True)
        except Exception: _LOGGER.exception("Failed to turn on CAME light %s",self._id); raise
    async def async_turn_off(self, **kwargs: Any)->None:
        self._optimistic_update(status=0)
        try: await self.hass.async_add_executor_job(self.coordinator.hub.switch,self._id,False,True)
        except Exception: _LOGGER.exception("Failed to turn off CAME light %s",self._id); raise
