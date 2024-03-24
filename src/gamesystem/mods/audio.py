from .modulebase import GameModule
import pygame.mixer
from pygame.mixer import Sound, Channel

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Dict


class AudioManagerNumChannels(GameModule):
	IDMARKER = "audio"

	@dataclass(slots=True, frozen=True)
	class AudioFile:
		path: str
		name: str
		idx: int
		file: Sound

		def play(self):
			pygame.mixer.find_channel(True).play(self.file)

	def create(self, sounds: Dict[str, str], num_channels: int = 20):
		pygame.mixer.init()
		self.sounds = self._loadsounds(sounds)
		pygame.mixer.set_num_channels(num_channels)

	def _loadsounds(self, sounds):
		loaded = {}

		for i, pair in enumerate(sounds.items()):
			key, path = pair
			af = AudioManagerNumChannels.AudioFile(path=path, name=key, idx=i, file=Sound(path))

			loaded[key] = af

		return SimpleNamespace(**loaded)
