"""DataUpdateCoordinator for the Came Eti Domo integration."""
from __future__ import annotations
from datetime import timedelta
import logging
import requests
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.debounce import Debouncer
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import CONF_HOST, DEFAULT_SCAN_INTERVAL, DOMAIN
from .eti_domo import CommandNotFound, Domo, RequestError, ServerNotFound

_LOGGER = logging.getLogger(__name__)
FEATURE_TO_KEY = {"lights":"lights","openings":"openings","relays":"relays","thermoregulation":"thermo","analogin":"analogin"}

class CameCoordinator(DataUpdateCoordinator[dict]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, hub: Domo) -> None:
        super().__init__(hass,_LOGGER,config_entry=entry,name=f"{DOMAIN} ({entry.data[CONF_HOST]})",update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),request_refresh_debouncer=Debouncer(hass,_LOGGER,cooldown=0.25,immediate=True))
        self.hub=hub
        self._features:set[str]|None=None
    def _fetch(self)->dict:
        hub=self.hub
        if self._features is None:
            features=hub.list_request(Domo.available_commands["features"]).get("list",[])
            self._features=set(features)&set(FEATURE_TO_KEY)
            _LOGGER.debug("ETI/Domo features: %s",self._features)
        data={key:{} for key in FEATURE_TO_KEY.values()}
        if "lights" in self._features:
            floors=hub.list_request(Domo.available_commands["lights"]).get("array",[])
            for floor in floors:
                for room in floor.get("array",[]):
                    for item in room.get("array",[]):
                        data["lights"][item["act_id"]]={**item,"floor_name":floor.get("name",""),"room_name":room.get("name","")}
        if "openings" in self._features:
            openings=hub.list_request(Domo.available_commands["openings"]).get("array",[])
            data["openings"]={item["open_act_id"]:item for item in openings}
        if "relays" in self._features:
            relays=hub.list_request(Domo.available_commands["relays"]).get("array",[])
            data["relays"]={item["act_id"]:item for item in relays}
        if "thermoregulation" in self._features:
            thermos=hub.list_request(Domo.available_commands["thermoregulation"]).get("array",[])
            data["thermo"]={item["act_id"]:item for item in thermos}
        if "analogin" in self._features:
            analogs=hub.list_request(Domo.available_commands["analogin"]).get("array",[])
            data["analogin"]={item["act_id"]:item for item in analogs}
        return data
    async def _async_update_data(self)->dict:
        try:
            return await self.hass.async_add_executor_job(self._fetch)
        except (RequestError,CommandNotFound,ServerNotFound,requests.RequestException,ValueError,KeyError) as err:
            raise UpdateFailed(f"Error communicating with ETI/Domo: {err}") from err
