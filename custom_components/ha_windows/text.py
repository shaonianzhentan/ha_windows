from homeassistant.components.text import TextEntity
from .manifest import manifest, get_device_info

async def async_setup_entry(
    hass,
    entry,
    async_add_entities,
) -> None:
    async_add_entities([
        WindowsInputText(hass, entry)
    ], True)

class WindowsText(TextEntity):
   
    def __init__(self, hass, entry, name):
        super().__init__()
        self.hass = hass
        config = entry.data
        self.dev_id = config.get('dev_id')
        self.dev_name = config.get('name')
        self._attr_unique_id = f"{entry.entry_id}{name}"
        self._attr_name = f"{self.dev_name}{name}"
        self.last_frame = None

    @property
    def device_info(self):
        return get_device_info(self.dev_id, self.dev_name)

    @property
    def windows_device(self):
      return self.hass.data[manifest.domain].device[self.dev_id]

    def call_windows(self, type, data = ''):
        self.hass.bus.fire(manifest.domain, { 'dev_id': self.dev_id, 'type': type, 'data': data })

class WindowsInputText(WindowsText):

    def __init__(self, hass, entry):
        super().__init__(hass, entry, '文本输入')
        self._attr_icon = 'mdi:receipt-text-send'
        self._attr_native_value = ''

    async def async_set_value(self, value: str) -> None:
        self.call_windows('input_text', value)
        self._attr_native_value = value