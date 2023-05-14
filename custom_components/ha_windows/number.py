from homeassistant.components.number import NumberEntity
from .manifest import manifest, get_device_info

async def async_setup_entry(
    hass,
    entry,
    async_add_entities,
) -> None:
    async_add_entities([
        SystemVolumeNumber(hass, entry)
    ], True)

class WindowsNumber(NumberEntity):
   
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


class SystemVolumeNumber(WindowsNumber):

    def __init__(self, hass, entry):
        super().__init__(hass, entry, '音量')
        self.windows_device.append(self)
        self._attr_native_value = 100

    def windows_event(self, dev_id, msg_type, msg_data):
        if dev_id == self.dev_id:
            if msg_type == 'updated':
              self._attr_native_value = int(msg_data.get('system_volume', 100))

    async def async_update(self):
      if self._attr_native_value > 70:
        self._attr_icon = 'mdi:volume-high'
      elif self._attr_native_value > 40:
        self._attr_icon = 'mdi:volume-medium'
      else:
        self._attr_icon = 'mdi:volume-low'

    async def async_set_native_value(self, value: float) -> None:
      self._attr_native_value = value
      self.call_windows('set_volume', value)