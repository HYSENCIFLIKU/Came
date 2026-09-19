"""The Came Eti Domo integration."""
from __future__ import annotations

import logging
import requests
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from .const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, DOMAIN
from .coordinator import CameCoordinator
from .eti_domo import Domo, ServerNotFound

_LOGGER = logging.getLogger(__name__)
PLATFORMS: list[Platform] = [Platform.CLIMATE, Platform.COVER, Platform.LIGHT, Platform.SENSOR, Platform.SWITCH]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Came Eti Domo from a config entry."""
    host = entry.data[CONF_HOST]
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]
    def create_hub() -> Domo:
        hub = Domo(host)
        if not hub.login(username, password):
            raise ConfigEntryAuthFailed("Invalid eti/domo credentials")
        return hub
    try:
        hub = await hass.async_add_executor_job(create_hub)
    except (ServerNotFound, requests.RequestException) as err:
        raise ConfigEntryNotReady(f"Cannot connect to eti/domo at {host}") from err
    coordinator = CameCoordinator(hass, entry, hub)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
