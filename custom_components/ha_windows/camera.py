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

import io, time, aiohttp, base64
from urllib.parse import urlparse
from .manifest import manifest, get_device_info

async def async_setup_entry(
    hass,
    entry,
    async_add_entities,
) -> None:
    async_add_entities([
        ComputerCamera(hass, entry)
    ], True)

class WindowsCamera(Camera):
   
    def __init__(self, hass, entry, name):
        super().__init__()
        self.hass = hass
        config = entry.data
        self.dev_id = config.get('dev_id')
        self.dev_name = config.get(CONF_NAME)
        self._attr_unique_id = f"{entry.entry_id}{name}"
        self._attr_name = f"{self.dev_name}{name}"
        self.last_frame = None

    @property
    def device_info(self):
        return get_device_info(self.dev_id, self.dev_name)

    @property
    def windows_device(self):
      return self.hass.data[manifest.domain].device[self.dev_id]

class ComputerCamera(WindowsCamera):

    def __init__(self, hass, entry):
        super().__init__(hass, entry, '截图')
        self._attr_entity_picture = 'https://bingw.jasonzeng.dev/?v'
        self.windows_device.append(self)

    def windows_event(self, dev_id, msg_type, msg_data):
        if dev_id == self.dev_id:
            if msg_type == 'screenshot':
                self.last_frame = base64.b64decode(msg_data)

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return a still image response from the camera."""
        if self.last_frame is None:
            async with aiohttp.ClientSession() as session:
                async with session.get(self._attr_entity_picture) as resp:
                    self.last_frame = await resp.content.read()

        return self.last_frame