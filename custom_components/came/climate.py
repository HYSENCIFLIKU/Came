"""Climate platform for the Came Eti Domo integration."""
from __future__ import annotations
from typing import Any
from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature
from homeassistant.components.climate.const import HVACMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import slugify
from .const import DOMAIN
from .coordinator import CameCoordinator
from .entity import CameEntity
async def async_setup_entry(hass:HomeAssistant,config_entry:ConfigEntry,async_add_entities:AddEntitiesCallback)->None:
    coordinator:CameCoordinator=hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities(CameClimate(coordinator,item) for item in coordinator.data.get("thermo",{}).values())
class CameClimate(CameEntity,ClimateEntity):
    _attr_temperature_unit=UnitOfTemperature.CELSIUS
    _attr_supported_features=ClimateEntityFeature.TARGET_TEMPERATURE|ClimateEntityFeature.TURN_ON|ClimateEntityFeature.TURN_OFF
    _attr_hvac_modes=[HVACMode.OFF,HVACMode.AUTO,HVACMode.HEAT,HVACMode.COOL]
    _attr_min_temp=5.0; _attr_max_temp=35.0; _attr_target_temperature_step=0.1
    def __init__(self,coordinator:CameCoordinator,item:dict)->None:
        super().__init__(coordinator,"thermo",item["act_id"])
        object_id=item["name"].lower().replace(" ","_")+"_"+str(item["act_id"])
        self.entity_id="climate."+slugify(object_id); self._attr_unique_id="climate."+object_id; self._attr_name=item["name"]
    def _temp(self,key):
        item=self._item
        if not item or item.get(key) is None:return None
        try:
            value=float(item[key])
            return value/10 if abs(value)>100 else value
        except (TypeError,ValueError):return None
    @property
    def current_temperature(self):return self._temp("temp")
    @property
    def target_temperature(self):return self._temp("set_point")
    @property
    def current_humidity(self):
        item=self._item
        return None if not item else item.get("hygro")
    @property
    def hvac_mode(self):
        item=self._item
        if not item:return HVACMode.OFF
        mode=item.get("mode")
        if mode in (0,"0","off"):return HVACMode.OFF
        if mode in (2,"2","auto"):return HVACMode.AUTO
        return HVACMode.COOL if item.get("season") in ("summer","estate",1,"1") else HVACMode.HEAT
    async def async_set_temperature(self,**kwargs:Any)->None:
        temperature=kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:return
        mode=(self._item or {}).get("mode",1)
        await self.hass.async_add_executor_job(self.coordinator.hub.thermo_mode,self._id,mode,temperature)
        self._optimistic_update(set_point=temperature)
        await self.coordinator.async_request_refresh()
    async def async_set_hvac_mode(self,hvac_mode:HVACMode)->None:
        target=self.target_temperature or 20.0
        if hvac_mode==HVACMode.OFF:
            await self.hass.async_add_executor_job(self.coordinator.hub.thermo_mode,self._id,0,target); self._optimistic_update(mode=0)
        elif hvac_mode==HVACMode.AUTO:
            await self.hass.async_add_executor_job(self.coordinator.hub.thermo_mode,self._id,2,target); self._optimistic_update(mode=2)
        elif hvac_mode==HVACMode.HEAT:
            await self.hass.async_add_executor_job(self.coordinator.hub.change_season,"winter")
            await self.hass.async_add_executor_job(self.coordinator.hub.thermo_mode,self._id,1,target); self._optimistic_update(mode=1,season="winter")
        elif hvac_mode==HVACMode.COOL:
            await self.hass.async_add_executor_job(self.coordinator.hub.change_season,"summer")
            await self.hass.async_add_executor_job(self.coordinator.hub.thermo_mode,self._id,1,target); self._optimistic_update(mode=1,season="summer")
        await self.coordinator.async_request_refresh()
    async def async_turn_on(self)->None:
        target=self.target_temperature or 20.0
        await self.hass.async_add_executor_job(self.coordinator.hub.thermo_mode,self._id,1,target); self._optimistic_update(mode=1)
        await self.coordinator.async_request_refresh()
    async def async_turn_off(self)->None:
        target=self.target_temperature or 20.0
        await self.hass.async_add_executor_job(self.coordinator.hub.thermo_mode,self._id,0,target); self._optimistic_update(mode=0)
        await self.coordinator.async_request_refresh()
