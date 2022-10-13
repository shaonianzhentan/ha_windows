"""Support to interact with a Music Player Daemon."""
from __future__ import annotations

from contextlib import suppress
from datetime import timedelta, datetime
import logging
from typing import Any

import voluptuous as vol

from homeassistant.components.media_player import (
    BrowseMedia,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerDeviceClass,
)
from homeassistant.const import (
    STATE_OFF, 
    STATE_ON, 
    STATE_PLAYING, 
    STATE_PAUSED,
    STATE_UNAVAILABLE
)
from homeassistant.components.media_player.const import (
    MEDIA_TYPE_MUSIC
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

async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    config = entity.data    
    entity = HaWindowsMediaPlayer(hass, config['dev_id'])
    hass.data[entry.entry_id] == entity
    async_add_entities([entity], True)

class HaWindowsMediaPlayer(MediaPlayerEntity):

    _attr_media_content_type = MEDIA_TYPE_MUSIC

    # pylint: disable=no-member
    def __init__(self, hass, dev_id):
        self.hass = hass
        self._attr_unique_id = dev_id
        self._attr_name = manifest.name
        self._attr_media_image_remotely_accessible = True
        self._attr_device_class = MediaPlayerDeviceClass.TV.value
        
        self.playlist = []
        self.playindex = 0
        self._attr_media_position_updated_at = datetime.now()

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
        # 60秒无更新，则中断
        if datetime.now() - self._attr_media_position_updated_at > 60:
            self._attr_state = STATE_OFF

    async def async_set_volume_level(self, volume: float) -> None:
        self.call_windows_app('music_volume', volume)

    async def async_volume_up(self) -> None:
        self.call_windows_app('music_volume_up')

    async def async_volume_down(self) -> None:
        self.call_windows_app('music_volume_down')

    async def async_media_play(self) -> None:
        self.call_windows_app('music_play')

    async def async_media_pause(self) -> None:
        self.call_windows_app('music_pause')

    async def async_media_next_track(self) -> None:
        self.call_windows_app('music_next')

    async def async_media_previous_track(self) -> None:
        self.call_windows_app('music_previous')

    async def async_mute_volume(self, mute: bool) -> None:
        self.call_windows_app('music_mute', mute)

    async def async_set_repeat(self, repeat) -> None:
        self.call_windows_app('music_repeat', repeat)

    async def async_set_shuffle(self, shuffle: bool) -> None:
        self.call_windows_app('music_shuffle', shuffle)

    async def async_media_seek(self, position: float) -> None:
        self.call_windows_app('music_position', position)

    async def async_browse_media(
        self, media_content_type: str | None = None, media_content_id: str | None = None
    ) -> BrowseMedia:
        cloud_music = self.hass.data.get('cloud_music')
        if cloud_music is not None:
            return await cloud_music.async_browse_media(self, media_content_type, media_content_id)

    async def async_play_media(
        self, media_type: str, media_id: str, **kwargs: Any
    ) -> None:
        cloud_music = self.hass.data.get('cloud_music')
        if cloud_music is not None:
            result = await cloud_music.async_play_media(self, cloud_music, media_id)
            if result is not None:
                if result == 'index':
                    # 播放当前列表指定项
                    self.call_windows_app('music_index', self.playindex)
                elif result.startswith('http'):
                    # HTTP播放链接
                    pass
                else:
                    # 添加播放列表到播放器
                    self.load_playlist()
        else:
            self.call_windows_app('music_url', media_id)

    def call_windows_app(self, type, data = ''):
        ha = self.hass.data[manifest.domain]
        ha.fire_event({
            'dev_id': self._attr_unique_id,
            'type': type,
            'data': data
        })

    def load_playlist(self):
        arr = []
        for item in self.playlist:
            arr.append(item.url)
        self.call_windows_app('music_load', arr)
