from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.const import CONF_NAME
from .manifest import manifest, get_device_info

async def async_setup_entry(
    hass,
    entry,
    async_add_entities,
) -> None:
    async_add_entities([
      LockScreenBinarySensor(hass, entry)
    ], True)

class WindowsBinarySensor(BinarySensorEntity):

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

class LockScreenBinarySensor(WindowsBinarySensor):

  def __init__(self, hass, entry):
    super().__init__(hass, entry, '锁屏状态')
    self.windows_device.append(self)

  def windows_event(self, dev_id, msg_type, msg_data):
    if dev_id == self.dev_id:
        if msg_type == 'system_event':
            if msg_data == '屏幕锁定':
                self._attr_is_on = True
                self._attr_icon = 'mdi:monitor-lock'
            elif msg_data == '屏幕解锁':
                self._attr_is_on = False                
                self._attr_icon = 'mdi:monitor-dashboard'