import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntry
from datetime import timedelta, datetime

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
        hass.services.async_register(manifest.domain, 'shutdown', self.shutdown)

    async def update_tile(self, service) -> None:
        data = service.data
        self.call_windows_app(data.get('entity_id'), 'update_tile', {
            'from': data.get('from'),
            'subject': data.get('subject'),
            'body': data.get('body')
        })

    async def clear_tile(self, service) -> None:
        data = service.data
        self.call_windows_app(data.get('entity_id'), 'clear_tile', '')

    async def tts_say(self, service) -> None:
        data = service.data
        text = data.get('text', '')
        self.call_windows_app(data.get('entity_id'), 'tts', text)

    async def exec_cmd(self, service) -> None:
        data = service.data
        text = data.get('text', '')
        self.call_windows_app(data.get('entity_id'), 'cmd', text)

    async def shutdown(self, service) -> None:
        data = service.data
        second = data.get('second', 60)
        self.call_windows_app(data.get('entity_id'), 'cmd', f"shutdown -s -f -t {second}")

    # 服务调用windows应用
    def call_windows_app(self, entity_id, type, data):
        state = self.hass.states.get(entity_id)
        dev_id = state.attributes.get('app_id')
        # print(dev_id)
        self.fire_event({
            'dev_id': dev_id,
            'type': type,
            'data': data
        })

    # 消息接收
    def receive_data(self, hass, connection, msg):
        self.connection = connection

        data = msg['data']
        # print(data)

        dev_id = data.get('dev_id')
        msg_type = data.get('type', '')
        msg_data = data.get('data', {})

        player = hass.data.get(dev_id)

        if player is None:
            return

        if msg_type == 'init':
            # 初始化数据
            player.init_playlist()

            player._attr_media_position_updated_at = datetime.now()
            player._attr_state = STATE_ON
        elif msg_type == 'music_info':
            # 更新
            state = msg_data.get('state')
            if state == 'playing':
                state = STATE_PLAYING
            elif state == 'paused':
                state = STATE_PAUSED
            else:
                state = STATE_ON
            
            playindex = msg_data.get('index', 0)
            if  player.playindex != playindex and len(player.playlist) > playindex:
                player.playindex = playindex
                player.load_music_info()

            player._attr_state = state
            player._attr_media_position = msg_data.get('media_position', 0)
            player._attr_media_duration = msg_data.get('media_duration', 0)
            player._attr_volume_level = msg_data.get('volume')
            player._attr_repeat = msg_data.get('repeat')
            player._attr_shuffle = msg_data.get('shuffle')
            player._attr_is_volume_muted = msg_data.get('muted')
            player._attr_media_position_updated_at = datetime.now()
        elif msg_type == 'music_pong':
            # 判断是否在线
            player._attr_media_position_updated_at = datetime.now()
            if player._attr_state == STATE_OFF:
                player._attr_state = STATE_ON

    def fire_event(self, data):
        # print(data)
        self.hass.bus.fire(manifest.domain, data)