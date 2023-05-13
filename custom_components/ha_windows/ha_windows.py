import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntry
from datetime import timedelta, datetime
from urllib.parse import quote
from homeassistant.helpers import template
from homeassistant.const import (
    STATE_OFF, 
    STATE_ON, 
    STATE_PLAYING, 
    STATE_PAUSED,
    STATE_UNAVAILABLE
)

from .const import PLATFORMS
from .manifest import manifest

HA_WINDOWS_SERVER = "ha_windows_server"
SCHEMA_WEBSOCKET = websocket_api.BASE_COMMAND_MESSAGE_SCHEMA.extend(
    {
        "type": HA_WINDOWS_SERVER,
        vol.Optional("data"): dict,
    }
)

class HaWindows():

    def __init__(self, hass):
        self.hass = hass
        self.connection = None
        # 全部设备
        self.device = {}
        hass.components.websocket_api.async_register_command(
            HA_WINDOWS_SERVER,
            self.receive_data,
            SCHEMA_WEBSOCKET
        )
        # 注册服务
        hass.services.async_register(manifest.domain, 'update_tile', self.update_tile)
        hass.services.async_register(manifest.domain, 'clear_tile', self.clear_tile)

        hass.services.async_register(manifest.domain, 'tts', self.tts_say)

        hass.services.async_register(manifest.domain, 'cmd', self.exec_cmd)
        hass.services.async_register(manifest.domain, 'start', self.exec_start)
        hass.services.async_register(manifest.domain, 'shutdown', self.exec_shutdown)

        hass.services.async_register(manifest.domain, 'keyboard', self.exec_keyboard)
        hass.services.async_register(manifest.domain, 'mouse_click', self.exec_mouse_click)
        hass.services.async_register(manifest.domain, 'mouse_pos', self.exec_mouse_pos)
        hass.services.async_register(manifest.domain, 'mouse_move', self.exec_mouse_move)

    async def tts_say(self, service) -> None:
        data = service.data
        text = data.get('text', '')
        self.call_windows(data.get('entity_id'), 'tts', text)

    # region 命令

    async def exec_cmd(self, service) -> None:
        data = service.data
        cmd = data.get('text')
        self.exec_homeassistant(data.get('entity_id'), f"cmd={quote(cmd)}")

    async def exec_start(self, service) -> None:
        data = service.data
        cmd = 'start "HA" ' + data.get('text', '')
        self.exec_homeassistant(data.get('entity_id'), f"cmd={quote(cmd)}")

    async def exec_shutdown(self, service) -> None:
        data = service.data
        cmd = f"shutdown -s -f -t {data.get('second', 60)}"
        self.exec_homeassistant(data.get('entity_id'), f"cmd={quote(cmd)}")

    # endregion

    # region 键盘 & 鼠标操作

    async def exec_keyboard(self, service) -> None:
        data = service.data
        keys = data.get('keys').lower()
        self.exec_homeassistant(data.get('entity_id'), f"keyboard={quote(keys)}")

    async def exec_mouse_click(self, service) -> None:
        data = service.data
        click = data.get('click').lower()
        self.exec_homeassistant(data.get('entity_id'), f"mouse_click={quote(click)}")

    async def exec_mouse_pos(self, service) -> None:
        data = service.data
        point = f"{data.get('x')},{data.get('y')}"
        self.exec_homeassistant(data.get('entity_id'), f"mouse_pos={quote(point)}")

    async def exec_mouse_move(self, service) -> None:
        data = service.data
        point = f"{data.get('x')},{data.get('y')}"
        self.exec_homeassistant(data.get('entity_id'), f"mouse_move={quote(point)}")

    # endregion

    # region 磁贴

    async def update_tile(self, service) -> None:
        data = service.data
        self.call_windows(data.get('entity_id'), 'update_tile', {
            'from': data.get('from'),
            'subject': data.get('subject'),
            'body': data.get('body')
        })

    async def clear_tile(self, service) -> None:
        data = service.data
        self.call_windows(data.get('entity_id'), 'clear_tile', '')

    # endregion

    # region 服务

    def exec_homeassistant(self, entity_id, data):
        self.call_windows(entity_id, 'homeassistant://', f"?{data}")

    # 服务调用windows应用
    def call_windows(self, entity_id, type, data):
        dev_id =  self.template("{{device_attr('" + entity_id + "', 'identifiers') ) | first | first}}")
        self.hass.bus.fire(manifest.domain, { 'dev_id': dev_id, 'type': type, 'data': data })

    # endregion
    
    # 模板解析
    def template(self, _message):
        tpl = template.Template(_message, self.hass)
        _message = tpl.async_render(None)
        return _message

    # 消息接收
    def receive_data(self, hass, connection, msg):
        self.connection = connection

        data = msg['data']

        dev_id = data.get('dev_id')
        msg_type = data.get('type', '')
        msg_data = data.get('data', {})

        if dev_id is not None or dev_id != '':
            entities = self.device.get(dev_id)
            if entities is not None:
                for entity in entities:
                    if hasattr(entity, 'windows_event'):
                        entity.windows_event(dev_id, msg_type, msg_data)