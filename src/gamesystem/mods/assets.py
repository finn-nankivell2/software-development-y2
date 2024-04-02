from .modulebase import GameModule
from typing import Dict
import pygame.image
from pygame import Surface
from dataclasses import dataclass
import logging


@dataclass(slots=True, frozen=True)
class AssetEntry:
	path: str
	img: Surface


# TODO: Investigate wrong asset being used randomly
class AssetManager(GameModule):
	IDMARKER = "assets"

	def create(self, assets: Dict[str, str]):
		self._assets = {}
		for pair in assets.items():
			self._load(*pair)

	def _load(self, name, path):
		if name in self.__dict__:
			raise TypeError(f"{name} already present")

		img = pygame.image.load(path).convert_alpha()
		self.__dict__[name] = img
		self._assets[name] = AssetEntry(path, img)
		logging.debug(f"Loaded {name} = {img} from path: {path}")

	def add(self, name, path):
		self._load(name, path)

	def get(self, name) -> Surface:
		return self.__dict__[name]

	def get_entry(self, name) -> AssetEntry:
		return self._assets[name]

	def all(self) -> Dict[str, AssetEntry]:
		return self._assets
