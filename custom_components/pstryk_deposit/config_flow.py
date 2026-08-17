"""Config flow for Pstryk Prosumer Deposit."""
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import PstrykJwtClient
from .const import DOMAIN, CONF_EMAIL, CONF_PASSWORD


class PstrykDepositConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            session = async_get_clientsession(self.hass)
            client = PstrykJwtClient(
                email=user_input[CONF_EMAIL],
                password=user_input[CONF_PASSWORD],
                session=session,
            )
            if await client.test_auth():
                await self.async_set_unique_id(user_input[CONF_EMAIL])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Pstryk Deposit ({user_input[CONF_EMAIL]})",
                    data=user_input,
                )
            else:
                errors["base"] = "invalid_auth"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_EMAIL): str,
                vol.Required(CONF_PASSWORD): str,
            }),
            errors=errors,
        )
