"""Config flow for UDP Listener."""
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN

class UDPListenerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for UDP Listener."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """User config step."""
        errors = {}

        if user_input is not None:
            port = user_input["port"]
            update_interval = user_input["update_interval"]
            
            if 1024 <= port <= 65535:
                if 1 <= update_interval <= 3600:  # 1 Sekunde bis 1 Stunde
                    return self.async_create_entry(
                        title="UDP Listener", 
                        data=user_input
                    )
                else:
                    errors["update_interval"] = "invalid_interval"
            else:
                errors["port"] = "invalid_port"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("port", default=12345): vol.All(
                    vol.Coerce(int), 
                    vol.Range(min=1024, max=65535)
                ),
                vol.Required("update_interval", default=5): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=1, max=3600)
                )
            }),
            errors=errors,
            description_placeholders={
                "min_interval": "1",
                "max_interval": "3600"
            }
        )