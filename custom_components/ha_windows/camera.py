from __future__ import annotations

import voluptuous as vol

from homeassistant.components.camera import (
    DEFAULT_CONTENT_TYPE,
    PLATFORM_SCHEMA,
    Camera,
    SUPPORT_STREAM,
)
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

import io, time
from urllib.parse import urlparse
from .manifest import manifest

async def async_setup_entry(
    hass,
    entry,
    async_add_entities,
) -> None:
    async_add_entities([WindowsCamera(hass, entry)], True)

class WindowsCamera(Camera):
   
    def __init__(self, hass, entry):
        self.hass = hass
        config = entry.data
        self._attr_unique_id = entry.entry_id
        self.device_name = config.get(CONF_NAME)
        self._attr_name = f"{self.device_name}屏幕显示"

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return a still image response from the camera."""
        return ''
    
    @property
    def device_info(self):
        return {
            'identifiers': {
                (manifest.domain, manifest.documentation)
            },
            'name': self.device_name,
            'manufacturer': 'shaonianzhentan',
            'model': 'Windows',
            'sw_version': manifest.version
        }