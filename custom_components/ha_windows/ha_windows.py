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

    # 消息接收
    def receive_data(self, hass, connection, msg):
        self.connection = connection

        data = msg['data']
        print(data)

        dev_id = data.get('dev_id')
        msg_type = data.get('type', '')
        msg_data = data.get('data', {})

        player = hass.data.get(dev_id)

        if player is None:
            return

        if msg_type == 'init':
            # 初始化数据
            player.init_playlist()
        elif msg_type == 'music_info':
            # 更新
            state = msg_data.get('state')
            if state == 'playing':
                state = STATE_PLAYING
            elif state == 'paused':
                state = STATE_PAUSED
            else:
                state = STATE_ON

            print(player)
            playindex = msg_data.get('index', 0)
            if  player.playindex != playindex and len(player.playlist) > playindex:
                player.playindex = playindex
                music_info = player.playlist[playindex]
                player._attr_app_name = music_info.singer
                player._attr_media_image_url = music_info.thumbnail
                player._attr_media_album_name = music_info.album
                player._attr_media_title = music_info.song
                player._attr_media_artist = music_info.singer

            player._attr_state = state
            player._attr_media_position = msg_data.get('media_position', 0)
            player._attr_media_duration = msg_data.get('media_duration', 0)
            player._attr_volume_level = msg_data.get('volume')
            player._attr_repeat = msg_data.get('repeat')
            player._attr_shuffle = msg_data.get('shuffle')
            player._attr_muted = msg_data.get('muted')
            player._attr_media_position_updated_at = datetime.now()

    def fire_event(self, data):
        print(data)
        self.hass.bus.fire(manifest.domain, data)