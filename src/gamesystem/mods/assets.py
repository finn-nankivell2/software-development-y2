from .modulebase import GameModule
from typing import Dict
import pygame.image


class AssetManager(GameModule):
	IDMARKER = "assets"

	def create(self, **kwargs: Dict[str, str]):
		self._assets = {}
		for pair in kwargs.items():
			self._load(*pair)

	def _load(self, name, path):
		if name in self.__dict__: raise TypeError(f"{name} already present")
		self.__dict__[name] = pygame.image.load(path).convert_alpha()

	def add(self, name, path):
		self._load(name, path)

	def get(self, name):
		return self.__dict__[name]
