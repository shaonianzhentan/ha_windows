from homeassistant.components.sensor import SensorEntity
from homeassistant.const import CONF_NAME
from .manifest import manifest, get_device_info

async def async_setup_entry(
    hass,
    entry,
    async_add_entities,
) -> None:
    async_add_entities([
      SystemEventSensor(hass, entry)
    ], True)

class WindowsSensor(SensorEntity):

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

class SystemEventSensor(WindowsSensor):

  def __init__(self, hass, entry):
    super().__init__(hass, entry, '事件')
    self.windows_device.append(self)    
    self._attr_icon = 'mdi:microsoft-windows'
    self._attr_native_value = manifest.version

  def windows_event(self, dev_id, msg_type, msg_data):
    if dev_id == self.dev_id:
        if msg_type == 'system_event':
            self._attr_native_value = msg_data