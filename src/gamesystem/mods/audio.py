from .modulebase import GameModule
import pygame.mixer
from pygame.mixer import Sound, Channel

from dataclasses import dataclass
from types import SimpleNamespace


class AudioManager(GameModule):
	IDMARKER = "audio"

	@dataclass(slots=True, frozen=True)
	class AudioFile:
		path: str
		name: str
		idx: int
		file: Sound
		channel: Channel

		def play(self):
			self.channel.play(self.file)

	def create(self, sounds):
		pygame.mixer.init()
		self.sounds = self._loadsounds(sounds)

	def _loadsounds(self, sounds):
		loaded = {}
		pygame.mixer.set_num_channels(len(sounds))

		for i, pair in enumerate(sounds.items()):
			key, path = pair
			af = AudioManager.AudioFile(path=path, name=key, idx=i, file=Sound(path), channel=Channel(i))

			loaded[key] = af

		return SimpleNamespace(**loaded)
