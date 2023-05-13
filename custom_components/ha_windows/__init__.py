from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv

from .const import PLATFORMS
from .manifest import manifest
from .ha_windows import HaWindows

DOMAIN = manifest.domain

CONFIG_SCHEMA = cv.deprecated(DOMAIN)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    # 初始化服务
    windows = hass.data.get(manifest.domain)
    if windows is None:
        windows = HaWindows(hass)
        hass.data.setdefault(manifest.domain, windows)

    windows.device[entry.data.get('dev_id')] = []

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(update_listener))
    return True

async def update_listener(hass, entry):
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:    
    windows = hass.data.get(manifest.domain)
    if windows is not None:
        del windows.device[entry.data.get('dev_id')]

    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

