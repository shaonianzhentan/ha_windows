from __future__ import annotations

from typing import Any
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, OptionsFlow, ConfigEntry
from homeassistant.data_entry_flow import FlowResult
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PASSWORD, CONF_PORT
from homeassistant.helpers.storage import STORAGE_DIR
from homeassistant.core import callback

from .manifest import manifest

DATA_SCHEMA = vol.Schema({
    vol.Required('name', default='Windows设备'): str,
    vol.Required('dev_id'): str
})

class SimpleConfigFlow(ConfigFlow, domain=manifest.domain):

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:

        errors = {}
        if user_input is not None:
            windows = hass.data.get(manifest.domain)
            if windows is not None and windows.device.get(user_input.get('dev_id')) is not None:
                return self.async_abort(reason="single_instance_allowed")

            return self.async_create_entry(title=user_input['name'], data=user_input)

        return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA, errors=errors)