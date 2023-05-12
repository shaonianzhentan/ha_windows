from homeassistant.components.sensor import SensorEntity
from homeassistant.const import CONF_NAME
from .manifest import manifest

async def async_setup_entry(
    hass,
    entry,
    async_add_entities,
) -> None:
    async_add_entities([
      SystemEventSensor(hass, entry)
    ], True)

class WindowsSensor(SensorEntity):

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

class SystemEventSensor(WindowsSensor):

  def __init__(self, hass, entry):
    super().__init__(hass, entry, '系统事件', 'microsoft-windows')
    self._attr_native_value = manifest.version