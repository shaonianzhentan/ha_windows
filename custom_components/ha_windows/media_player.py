"""Support to interact with a Music Player Daemon."""
from __future__ import annotations

from contextlib import suppress
from datetime import timedelta
import hashlib
import logging
import os
from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.components.media_player import (
    BrowseMedia,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerDeviceClass,
)
from homeassistant.const import (
    CONF_HOST, CONF_NAME, CONF_PASSWORD, CONF_PORT,    
    STATE_OFF, 
    STATE_ON, 
    STATE_PLAYING, 
    STATE_PAUSED,
    STATE_UNAVAILABLE
)
from homeassistant.components.media_player.const import (
    MEDIA_CLASS_ALBUM,
    MEDIA_CLASS_ARTIST,
    MEDIA_CLASS_CHANNEL,
    MEDIA_CLASS_DIRECTORY,
    MEDIA_CLASS_EPISODE,
    MEDIA_CLASS_MOVIE,
    MEDIA_CLASS_MUSIC,
    MEDIA_CLASS_PLAYLIST,
    MEDIA_CLASS_SEASON,
    MEDIA_CLASS_TRACK,
    MEDIA_CLASS_TV_SHOW,
    MEDIA_TYPE_ALBUM,
    MEDIA_TYPE_ARTIST,
    MEDIA_TYPE_CHANNEL,
    MEDIA_TYPE_EPISODE,
    MEDIA_TYPE_MUSIC,
    MEDIA_TYPE_MOVIE,
    MEDIA_TYPE_PLAYLIST,
    MEDIA_TYPE_SEASON,
    MEDIA_TYPE_TRACK,
    MEDIA_TYPE_TVSHOW,
    REPEAT_MODE_ALL,
    REPEAT_MODE_OFF,
    REPEAT_MODE_ONE,
    REPEAT_MODES
)
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util import Throttle
import homeassistant.util.dt as dt_util

_LOGGER = logging.getLogger(__name__)

from .manifest import manifest

PLAYLIST_UPDATE_INTERVAL = timedelta(seconds=120)

SUPPORT_MPD = (
    MediaPlayerEntityFeature.PAUSE
    | MediaPlayerEntityFeature.PREVIOUS_TRACK
    | MediaPlayerEntityFeature.NEXT_TRACK
    | MediaPlayerEntityFeature.PLAY_MEDIA
    | MediaPlayerEntityFeature.PLAY
    | MediaPlayerEntityFeature.CLEAR_PLAYLIST
    | MediaPlayerEntityFeature.REPEAT_SET
    | MediaPlayerEntityFeature.SHUFFLE_SET
    | MediaPlayerEntityFeature.SEEK
    | MediaPlayerEntityFeature.STOP
    | MediaPlayerEntityFeature.TURN_OFF
    | MediaPlayerEntityFeature.TURN_ON
    | MediaPlayerEntityFeature.BROWSE_MEDIA
)

HA_WINDOWS_SERVER = "ha_windows_server"
HA_WINDOWS_CLIENT = "ha_windows_client"
SCHEMA_WEBSOCKET = websocket_api.BASE_COMMAND_MESSAGE_SCHEMA.extend(
    {
        "type": HA_WINDOWS_SERVER,
        vol.Optional("data"): dict,
    }
)

async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:

    entity = HaWindowsMediaPlayer()
    
    hass.components.websocket_api.async_register_command(
            HA_WINDOWS_SERVER,
            entity.ws_receive_data,
            SCHEMA_WEBSOCKET
        )
    async_add_entities([entity], True)


class HaWindowsMediaPlayer(MediaPlayerEntity):
    """Representation of a MPD server."""

    _attr_media_content_type = MEDIA_TYPE_MUSIC

    # pylint: disable=no-member
    def __init__(self):

        self._attr_name = manifest.name
        self._attr_media_image_remotely_accessible = True
        self._attr_device_class = MediaPlayerDeviceClass.TV.value
        self._attr_unique_id = manifest.domain
        
        self.playlist = []
        self.playindex = 0

    # 消息接收
    def ws_receive_data(self, hass, connection, msg):
        data = msg['data']
        


    @property
    def device_info(self):
        return {
            'identifiers': {
                (manifest.domain, manifest.documentation)
            },
            'name': self.name,
            'manufacturer': 'shaonianzhentan',
            'model': 'CloudMusic',
            'sw_version': manifest.version
        }

    async def async_update(self) -> None:
        """Get the latest data and update the state."""
        # 判断是否断开连接

    async def async_select_source(self, source: str) -> None:
        print('选择源')

    async def async_set_volume_level(self, volume: float) -> None:
        print('音量')

    async def async_volume_up(self) -> None:
        pass

    async def async_volume_down(self) -> None:
        pass

    async def async_media_play(self) -> None:
        pass

    async def async_media_pause(self) -> None:
        pass

    async def async_media_stop(self) -> None:
        pass

    async def async_media_next_track(self) -> None:
        pass

    async def async_media_previous_track(self) -> None:
        pass

    async def async_mute_volume(self, mute: bool) -> None:
        pass

    async def async_play_media(
        self, media_type: str, media_id: str, **kwargs: Any
    ) -> None:
        cloud_music = self.hass.data.get('cloud_music')
        if cloud_music is not None:
            result = await cloud_music.async_play_media(self, cloud_music, media_id)
            if result is not None:
                if result == 'index':
                    # 播放当前列表指定项
                    await self._client.play(self.playindex)
                elif result.startswith('http'):
                    # HTTP播放链接
                    pass
                else:
                    # 添加播放列表到播放器
                    pass
    
    async def async_set_repeat(self, repeat) -> None:
        """Set repeat mode."""
        if repeat == REPEAT_MODE_OFF:
            pass
        else:
            if repeat == REPEAT_MODE_ONE:
                pass
            else:
                pass

    async def async_set_shuffle(self, shuffle: bool) -> None:
        pass

    async def async_turn_off(self) -> None:
        pass

    async def async_turn_on(self) -> None:
        pass

    async def async_media_seek(self, position: float) -> None:
        pass

    async def async_browse_media(
        self, media_content_type: str | None = None, media_content_id: str | None = None
    ) -> BrowseMedia:
        cloud_music = self.hass.data.get('cloud_music')
        if cloud_music is not None:
            return await cloud_music.async_browse_media(self, media_content_type, media_content_id)