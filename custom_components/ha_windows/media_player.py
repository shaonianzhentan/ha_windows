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
    SUPPORT_BROWSE_MEDIA,
    SUPPORT_TURN_OFF,
    SUPPORT_TURN_ON,
    SUPPORT_VOLUME_STEP,
    SUPPORT_VOLUME_SET,
    SUPPORT_VOLUME_MUTE,
    SUPPORT_SELECT_SOURCE,
    SUPPORT_SELECT_SOUND_MODE,
    SUPPORT_PLAY_MEDIA,
    SUPPORT_PLAY,
    SUPPORT_PAUSE,
    SUPPORT_SEEK,
    SUPPORT_CLEAR_PLAYLIST,
    SUPPORT_SHUFFLE_SET,
    SUPPORT_REPEAT_SET,
    SUPPORT_NEXT_TRACK,
    SUPPORT_PREVIOUS_TRACK,
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
from .ha_windows import HaWindows

SUPPORT_FEATURES = SUPPORT_VOLUME_STEP | SUPPORT_VOLUME_MUTE | SUPPORT_VOLUME_SET | \
    SUPPORT_SELECT_SOURCE | SUPPORT_SELECT_SOUND_MODE | \
    SUPPORT_PLAY_MEDIA | SUPPORT_PLAY | SUPPORT_PAUSE | SUPPORT_PREVIOUS_TRACK | SUPPORT_NEXT_TRACK | \
    SUPPORT_BROWSE_MEDIA | SUPPORT_SEEK | SUPPORT_CLEAR_PLAYLIST | SUPPORT_SHUFFLE_SET | SUPPORT_REPEAT_SET

async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    # 播放器
    config = entry.data
    dev_id = config['dev_id']
    entity = HaWindowsMediaPlayer(hass, dev_id)
    hass.data.setdefault(dev_id, entity)
    # 设置服务
    data = hass.data.get(manifest.domain)
    if data is None:
        hass.data.setdefault(manifest.domain, HaWindows(hass))

    async_add_entities([entity], True)

class HaWindowsMediaPlayer(MediaPlayerEntity):

    def __init__(self, hass, dev_id):
        self.hass = hass
        self._attr_unique_id = dev_id
        self._attr_media_image_remotely_accessible = True
        self._attr_device_class = MediaPlayerDeviceClass.TV.value
        self._attr_supported_features = SUPPORT_FEATURES
        
        # default attribute
        self._attr_source_list = []
        self._attr_sound_mode_list = []
        self._attr_name = manifest.name
        self._attr_state =  STATE_ON
        self._attr_volume_level = 1
        self._attr_repeat = 'all'
        self._attr_shuffle = False
        
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
        s = (datetime.now() - self._attr_media_position_updated_at).total_seconds()
        if s > 60:
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
        self.hass.data[manifest.domain].fire_event({
            'dev_id': self._attr_unique_id,
            'type': type,
            'data': data
        })

    def load_playlist(self):
        playlist = []
        for item in self.playlist:
            playlist.append(item.url)
        self.call_windows_app('music_load', {
            'playindex': self.playindex,
            'playlist': playlist
        })
        self.load_music_info()

    def init_playlist(self):
        playlist = []
        for item in self.playlist:
            playlist.append(item.url)
        self.call_windows_app('music_init', {
            'playindex': self.playindex,
            'playlist': playlist
        })
        self.load_music_info()

    def load_music_info(self):
        # 加载音乐信息
        if len(self.playlist) > self.playindex:
            music_info = self.playlist[self.playindex]
            self._attr_app_name = music_info.singer
            self._attr_media_image_url = music_info.thumbnail
            self._attr_media_album_name = music_info.album
            self._attr_media_title = music_info.song
            self._attr_media_artist = music_info.singer
            self._attr_media_content_id = music_info.url