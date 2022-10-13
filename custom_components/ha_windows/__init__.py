from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv

from .manifest import manifest
from .ha_windows import HaWindows

DOMAIN = manifest.domain
CONFIG_SCHEMA = cv.deprecated(DOMAIN)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data[DOMAIN] = HaWindows(hass)
    return True