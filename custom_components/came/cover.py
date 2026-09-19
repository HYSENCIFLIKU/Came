"""Cover platform for the Came Eti Domo integration."""
from __future__ import annotations
import logging
from typing import Any
from homeassistant.components.cover import CoverEntity, CoverEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import slugify
from .const import DOMAIN
from .coordinator import CameCoordinator
from .entity import CameEntity
from .eti_domo import Domo
_LOGGER=logging.getLogger(__name__)

async def async_setup_entry(hass:HomeAssistant,config_entry:ConfigEntry,async_add_entities:AddEntitiesCallback)->None:
    coordinator:CameCoordinator=hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities(Opening(coordinator,item) for item in coordinator.data.get("openings",{}).values())

class Opening(CameEntity,CoverEntity,RestoreEntity):
    _attr_assumed_state=True
    _attr_supported_features=CoverEntityFeature.OPEN|CoverEntityFeature.CLOSE|CoverEntityFeature.STOP
    def __init__(self,coordinator:CameCoordinator,item:dict)->None:
        super().__init__(coordinator,"openings",item["open_act_id"])
        object_id=item["name"].lower().replace(" ","_")+"_"+str(item["open_act_id"])
        self.entity_id="cover."+slugify(object_id); self._attr_unique_id="cover."+object_id; self._attr_name=item["name"]
        self._command_state:bool|None=None
    async def async_added_to_hass(self)->None:
        await super().async_added_to_hass()
        last_state=await self.async_get_last_state()
        if last_state is None:return
        if last_state.state=="open":self._command_state=False
        elif last_state.state=="closed":self._command_state=True
    @property
    def is_closed(self)->bool|None:
        if self._command_state is not None:return self._command_state
        item=self._item
        if item is None:return None
        status=item.get("status")
        if status==0:return True
        if status==1:return False
        return None
    async def async_open_cover(self,**kwargs:Any)->None:
        self._command_state=False; self.async_write_ha_state()
        try: await self.hass.async_add_executor_job(self.coordinator.hub.opening,self._id,Domo.opening_actions["open"])
        except Exception: _LOGGER.exception("Failed to open CAME cover %s",self._id); raise
    async def async_close_cover(self,**kwargs:Any)->None:
        self._command_state=True; self.async_write_ha_state()
        try: await self.hass.async_add_executor_job(self.coordinator.hub.opening,self._id,Domo.opening_actions["close"])
        except Exception: _LOGGER.exception("Failed to close CAME cover %s",self._id); raise
    async def async_stop_cover(self,**kwargs:Any)->None:
        self._command_state=None; self.async_write_ha_state()
        try: await self.hass.async_add_executor_job(self.coordinator.hub.opening,self._id,Domo.opening_actions["stop"])
        except Exception: _LOGGER.exception("Failed to stop CAME cover %s",self._id); raise
