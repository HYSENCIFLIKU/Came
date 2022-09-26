"""Component to interface openings."""
import logging

from homeassistant.core import HomeAssistant
from homeassistant.components.cover import CoverEntity, SUPPORT_OPEN, SUPPORT_CLOSE, SUPPORT_STOP

from .eti_domo import Domo, ServerNotFound

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_entities):
    """Set up a config entry."""

    # Get the Domo object
    hub = hass.data[DOMAIN]["hub"]
    # Retrieve the list of openings
    openings = (await hass.async_add_executor_job(hub.list_request, Domo.available_commands['openings']))['array']

    # Add all the openings
    async_add_entities(Opening(hub, opening) for opening in openings)


class Opening(CoverEntity):
    """Representation of a opening."""

    def __init__(self, hub: Domo, opening):
        """Init opening device."""
        self.entity_id = "cover." + opening['name'].lower().replace(" ", "_") + "_" + str(opening['open_act_id'])
        self._name = opening['name']
        self._id = opening['open_act_id']
        self._hub = hub
        self._status = opening['status']

    @property
    def unique_id(self):
        """Return unique ID for this device."""
        return self.entity_id

    @property
    def name(self):
        """Return the display name of this light."""
        return self._name

    @property
    def supported_features(self) -> int:
        return SUPPORT_OPEN | SUPPORT_CLOSE | SUPPORT_STOP

    def update(self):
        """Fetch new state data for this opening.
        This is the only method that should fetch new data for Home Assistant.
        """

        # Send a keep alive request
        self._hub.keep_alive()

        # Retrieve the list of openings
        openings = self._hub.list_request(Domo.available_commands['openings'])['array']

        # Search for the opening
        for opening in openings:
            if opening['open_act_id'] == self._id:
                # update the status
                _LOGGER.warning(str(opening))
                self._status = opening['status']

    @property
    def is_closed(self):
        return self._status == 0

    def open_cover(self, **kwargs):
        # Send a keep alive request
        self._hub.keep_alive()

        # Open cover
        self._hub.opening(self._id, Domo.opening_actions["open"])

        # Update the status
        self.update()

    def close_cover(self, **kwargs):
        # Send a keep alive request
        self._hub.keep_alive()

        # Open cover
        self._hub.opening(self._id, Domo.opening_actions["close"])

        # Update the status
        self.update()

    def stop_cover(self, **kwargs):
        # Send a keep alive request
        self._hub.keep_alive()

        # Open cover
        self._hub.opening(self._id, Domo.opening_actions["stop"])

        # Update the status
        self.update()
