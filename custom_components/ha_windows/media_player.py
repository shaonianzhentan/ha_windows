"""Support to interact with a Music Player Daemon."""
from __future__ import annotations

from contextlib import suppress
from datetime import timedelta, datetime
import logging
from typing import Any
from urllib.parse import quote
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
    STATE_UNAVAILABLE,
    CONF_NAME
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

from .manifest import manifest, get_device_info

SUPPORT_FEATURES = SUPPORT_VOLUME_STEP | SUPPORT_VOLUME_MUTE | SUPPORT_VOLUME_SET | \
    SUPPORT_SELECT_SOURCE | SUPPORT_SELECT_SOUND_MODE | \
    SUPPORT_PLAY_MEDIA | SUPPORT_PLAY | SUPPORT_PAUSE | SUPPORT_PREVIOUS_TRACK | SUPPORT_NEXT_TRACK | \
    SUPPORT_BROWSE_MEDIA | SUPPORT_SEEK | SUPPORT_CLEAR_PLAYLIST | SUPPORT_SHUFFLE_SET | SUPPORT_REPEAT_SET | \
    SUPPORT_TURN_ON | SUPPORT_TURN_OFF

async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    # 播放器
    async_add_entities([
        CloudMusicMediaPlayer(hass, entry),
        UniversallyMediaPlayer(hass, entry)
    ], True)

class WindowsMediaPlayer(MediaPlayerEntity):

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

    def call_windows(self, type, data = ''):
        self.hass.bus.fire(manifest.domain, { 'dev_id': self.dev_id, 'type': type, 'data': data })

    @property
    def windows_device(self):
      return self.hass.data[manifest.domain].device[self.dev_id]

class UniversallyMediaPlayer(WindowsMediaPlayer):

    def __init__(self, hass, entry):
        super().__init__(hass, entry, '通用播放器')
        self.windows_device.append(self)
        
    async def async_update(self) -> None:
        pass

    async def async_set_volume_level(self, volume: float) -> None:
        self._attr_volume_level = volume

    async def async_volume_up(self) -> None:
        volume_level = self._attr_volume_level + 0.1
        if volume_level > 1:
            volume_level = 1
        self._attr_volume_level = volume_level

    async def async_volume_down(self) -> None:
        volume_level = self._attr_volume_level - 0.1
        if volume_level < 0.1:
            volume_level = 0.1
        self._attr_volume_level = volume_level

    async def async_media_play(self) -> None:
        self._attr_state = STATE_PLAYING

    async def async_media_pause(self) -> None:
        self._attr_state = STATE_PAUSED

    async def async_media_next_track(self) -> None:
        self._attr_state = STATE_PAUSED

    async def async_media_previous_track(self) -> None:
        self._attr_state = STATE_PAUSED

    async def async_turn_off(self) -> None:
        pass

    async def async_turn_on(self) -> None:
        pass

    async def async_mute_volume(self, mute: bool) -> None:
        self._attr_is_volume_muted = mute


class CloudMusicMediaPlayer(WindowsMediaPlayer):

    def __init__(self, hass, entry):
        super().__init__(hass, entry, '云音乐播放器')
        self.windows_device.append(self)
        
        self._attr_media_image_remotely_accessible = True
        self._attr_device_class = MediaPlayerDeviceClass.TV.value
        self._attr_supported_features = SUPPORT_FEATURES
        self._attr_extra_state_attributes = { 'platform': 'cloud_music' }
        
        # default attribute
        self._attr_source_list = []
        self._attr_sound_mode_list = []
        self._attr_state =  STATE_ON
        self._attr_volume_level = 1
        self._attr_repeat = 'all'
        self._attr_shuffle = False
        
        self.playlist = []
        self.playindex = 0
        self._attr_media_position_updated_at = datetime.now()

    def windows_event(self, dev_id, msg_type, msg_data):
      if dev_id == self.dev_id:
        if msg_type == 'init':
          # 初始化数据
          self.init_playlist()

          self._attr_media_position_updated_at = datetime.now()
          self._attr_state = STATE_ON
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
            if  self.playindex != playindex and len(self.playlist) > playindex:
                self.playindex = playindex
                self.load_music_info()

            self._attr_state = state
            self._attr_media_position = msg_data.get('media_position', 0)
            self._attr_media_duration = msg_data.get('media_duration', 0)
            self._attr_volume_level = msg_data.get('volume')
            self._attr_repeat = msg_data.get('repeat')
            self._attr_shuffle = msg_data.get('shuffle')
            self._attr_is_volume_muted = msg_data.get('muted')
            self._attr_media_position_updated_at = datetime.now()
        elif msg_type == 'music_pong':
            # 判断是否在线
            self._attr_media_position_updated_at = datetime.now()
            if self._attr_state == STATE_OFF:
                self._attr_state = STATE_ON

    async def async_update(self) -> None:
        # 60秒无更新，则中断
        s = (datetime.now() - self._attr_media_position_updated_at).total_seconds()
        if s > 120:
            self._attr_state = STATE_OFF
        elif s > 60:
            # 判断是否在线
            self.call_windows('music_ping', '')

    async def async_set_volume_level(self, volume: float) -> None:
        self.call_windows('music_volume', volume)
        self._attr_volume_level = volume

    async def async_volume_up(self) -> None:
        self.call_windows('music_volume_up')
        volume_level = self._attr_volume_level + 0.1
        if volume_level > 1:
            volume_level = 1
        self._attr_volume_level = volume_level

    async def async_volume_down(self) -> None:
        self.call_windows('music_volume_down')
        volume_level = self._attr_volume_level - 0.1
        if volume_level < 0.1:
            volume_level = 0.1
        self._attr_volume_level = volume_level

    async def async_media_play(self) -> None:
        self.call_windows('music_play')
        self._attr_state = STATE_PLAYING

    async def async_media_pause(self) -> None:
        self.call_windows('music_pause')
        self._attr_state = STATE_PAUSED

    async def async_media_next_track(self) -> None:
        self.call_windows('music_next')
        self._attr_state = STATE_PAUSED

    async def async_media_previous_track(self) -> None:
        self.call_windows('music_previous')
        self._attr_state = STATE_PAUSED

    async def async_turn_off(self) -> None:
        ''' 关机命令 '''
        text = 'shutdown -s -f -t 10'
        self.call_windows('homeassistant://', f"?cmd={quote(text)}")

    async def async_turn_on(self) -> None:
        pass

    async def async_mute_volume(self, mute: bool) -> None:
        self.call_windows('music_mute', mute)
        self._attr_is_volume_muted = mute

    async def async_set_repeat(self, repeat) -> None:
        self.call_windows('music_repeat', repeat)
        self._attr_repeat = repeat

    async def async_set_shuffle(self, shuffle: bool) -> None:
        self.call_windows('music_shuffle', shuffle)
        self._attr_shuffle = shuffle

    async def async_media_seek(self, position: float) -> None:
        self.call_windows('music_position', position)
        self._attr_media_position = position

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
                    self.call_windows('music_index', self.playindex)
                    self.load_music_info()
                elif result.startswith('http'):
                    # HTTP播放链接
                    pass
                else:
                    # 添加播放列表到播放器
                    self.load_playlist()
        else:
            self.call_windows('music_url', media_id)

    def load_playlist(self):
        playlist = []
        for item in self.playlist:
            playlist.append(item.url)
        self.call_windows('music_load', {
            'playindex': self.playindex,
            'playlist': playlist
        })
        self.load_music_info()

    def init_playlist(self):
        playlist = []
        for item in self.playlist:
            playlist.append(item.url)
        self.call_windows('music_init', {
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