from homeassistant.components.button import ButtonEntity, ButtonDeviceClass
from homeassistant.const import CONF_NAME
from .manifest import manifest, get_device_info
from urllib.parse import quote

async def async_setup_entry(
    hass,
    entry,
    async_add_entities,
) -> None:
    async_add_entities([
      ScreenshotButton(hass, entry),
      CameraButton(hass, entry),
      ShutdownButton(hass, entry),
      LockButton(hass, entry),
      MonitorOffButton(hass, entry)
    ], True)

class WindowsButton(ButtonEntity):

    def __init__(self, hass, entry, name):
        super().__init__()
        self.hass = hass
        config = entry.data
        self.dev_id = config.get('dev_id')
        self.dev_name = config.get(CONF_NAME)
        self._attr_unique_id = f"{entry.entry_id}{name}"
        self._attr_name = f"{self.dev_name}{name}"

    @property
    def device_info(self):
        return get_device_info(self.dev_id, self.dev_name)

    @property
    def windows_device(self):
      return self.hass.data[manifest.domain].device[self.dev_id]

    def call_windows(self, type, data = ''):
        self.hass.bus.fire(manifest.domain, { 'dev_id': self.dev_id, 'type': type, 'data': data })

class ScreenshotButton(WindowsButton):

  def __init__(self, hass, entry):
        super().__init__(hass, entry, '屏幕')
        self._attr_icon = 'mdi:monitor-screenshot'

  async def async_press(self) -> None:
      self.call_windows('screenshot')

class CameraButton(WindowsButton):

  def __init__(self, hass, entry):
        super().__init__(hass, entry, '拍照')
        self._attr_icon = 'mdi:camera'

  async def async_press(self) -> None:
      self.call_windows('camera')

class ShutdownButton(WindowsButton):

  def __init__(self, hass, entry):
        super().__init__(hass, entry, '关机')
        self._attr_icon = 'mdi:power'

  async def async_press(self) -> None:
      self.call_windows('shutdown')

class LockButton(WindowsButton):

  def __init__(self, hass, entry):
        super().__init__(hass, entry, '锁屏')
        self._attr_icon = 'mdi:monitor-lock'

  async def async_press(self) -> None:
      self.call_windows('system_lock')

class MonitorOffButton(WindowsButton):

  def __init__(self, hass, entry):
        super().__init__(hass, entry, '熄屏')
        self._attr_icon = 'mdi:monitor-off'

  async def async_press(self) -> None:
      self.call_windows('monitorpower', False)