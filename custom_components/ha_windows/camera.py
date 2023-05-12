from __future__ import annotations

import voluptuous as vol

from homeassistant.components.camera import (
    DEFAULT_CONTENT_TYPE,
    PLATFORM_SCHEMA,
    Camera,
    CameraEntityFeature,
)
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

import io, time, aiohttp
from urllib.parse import urlparse
from .manifest import manifest

async def async_setup_entry(
    hass,
    entry,
    async_add_entities,
) -> None:
    async_add_entities([
        ScreenCamera(hass, entry),
        ComputerCamera(hass, entry)
    ], True)

class WindowsCamera(Camera):
   
    def __init__(self, hass, entry, name):
        super().__init__()
        self.hass = hass
        config = entry.data
        self._attr_unique_id = f"{entry.entry_id}{name}"
        self.device_name = config.get(CONF_NAME)
        self._attr_name = f"{self.device_name}{name}"
        self.last_frame = None

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

class ScreenCamera(WindowsCamera):

    def __init__(self, hass, entry):
        super().__init__(hass, entry, '屏幕')
        self._attr_entity_picture = 'https://bingw.jasonzeng.dev/?index=random'

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return a still image response from the camera."""
        if (width is not None and height is not None) or self.last_frame is None:
            async with aiohttp.ClientSession() as session:
                async with session.get(self._attr_entity_picture) as resp:
                    self.last_frame = await resp.content.read()

        return self.last_frame

class ComputerCamera(WindowsCamera):

    def __init__(self, hass, entry):
        super().__init__(hass, entry, '摄像头')
        self._attr_entity_picture = 'https://bingw.jasonzeng.dev/?index=random'

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return a still image response from the camera."""
        if (width is not None and height is not None) or self.last_frame is None:
            async with aiohttp.ClientSession() as session:
                async with session.get(self._attr_entity_picture) as resp:
                    self.last_frame = await resp.content.read()

        return self.last_frame