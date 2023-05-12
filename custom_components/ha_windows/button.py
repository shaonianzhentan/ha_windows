from homeassistant.components.button import ButtonEntity, ButtonDeviceClass
from homeassistant.const import CONF_NAME
from .manifest import manifest

async def async_setup_entry(
    hass,
    entry,
    async_add_entities,
) -> None:
    async_add_entities([
      ScreenshotButton(hass, entry),
      ShutdownButton(hass, entry),
      RebootButton(hass, entry),
      CameraButton(hass, entry)
    ], True)

class WindowsButton(ButtonEntity):

    def __init__(self, hass, entry, name, icon):
        super().__init__()
        self.hass = hass
        config = entry.data
        self._attr_unique_id = f"{entry.entry_id}{name}"
        self.device_name = config.get(CONF_NAME)
        self._attr_name = f"{self.device_name}{name}"
        self._attr_icon = f'mdi:{icon}'

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

class ScreenshotButton(WindowsButton):

  def __init__(self, hass, entry):
        super().__init__(hass, entry, '屏幕截图', 'monitor-screenshot')

  async def async_press(self) -> None:
      pass

class ShutdownButton(WindowsButton):

  def __init__(self, hass, entry):
        super().__init__(hass, entry, '关机', 'power')

  async def async_press(self) -> None:
      pass

class RebootButton(WindowsButton):

  def __init__(self, hass, entry):
        super().__init__(hass, entry, '重启', 'restart')

  async def async_press(self) -> None:
      pass

class CameraButton(WindowsButton):

  def __init__(self, hass, entry):
        super().__init__(hass, entry, '拍照', 'camera')

  async def async_press(self) -> None:
      pass