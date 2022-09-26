"""Config flow for Came Eti Domo integration."""
import logging
from typing import Any
import voluptuous as vol

from homeassistant import config_entries, core, exceptions

from .const import DOMAIN, CONF_HOST, CONF_USERNAME, CONF_PASSWORD  # pylint:disable=unused-import

from .eti_domo import Domo, ServerNotFound


_LOGGER = logging.getLogger(__name__)

# TODO adjust the data schema to the data that you need
DATA_SCHEMA = vol.Schema({CONF_HOST: str, CONF_USERNAME: str, CONF_PASSWORD: str})

async def validate_input(hass: core.HomeAssistant, data):
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """
    # TODO validate the data can be used to set up a connection.

    def validate(host, username, password) -> [Domo, Any]:
        domo_hub = None
        try:
            # Create an object representing the eti/domo with the host ip
            domo_hub = Domo(host)
        except ServerNotFound:
            raise CannotConnect
        # login to the server
        if not domo_hub.login(username, password):
            raise InvalidAuth
        domo_server_info = domo_hub.list_request(Domo.available_commands['features'])
        return domo_hub, domo_server_info

    hub, server_info = await hass.async_add_executor_job(validate, data["host"], data["username"], data["password"])
    # save the Domo object containing the client id session
    hass.data[DOMAIN] = {}
    hass.data[DOMAIN]["hub"] = hub

    # search for the unique id of the server
    serial = server_info['serial']

    #_LOGGER.error("Server host %s", hub.host, exc_info=1)

    # Return info that you want to store in the config entry.
    return {"title": serial}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Came Eti Domo."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self):
        """Initialize the Config flow."""
        self.config = None

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            try:

                # save user_input into the config parameter
                self.config = {
                    CONF_HOST: user_input[CONF_HOST],
                    CONF_USERNAME: user_input[CONF_USERNAME],
                    CONF_PASSWORD: user_input[CONF_PASSWORD]
                }

                # validate user input and login
                info = await validate_input(self.hass, user_input)

                # set unique id
                await self.async_set_unique_id(info['title'])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(title=info['title'], data=user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )

class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""
