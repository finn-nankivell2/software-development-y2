from gamesystem.mods.modulebase import GameModule
from dataclasses import dataclass
from pygame import Surface, Vector2
from typing import Optional, Dict, Union, Tuple
from gameutil import surface_region


@dataclass
class CachedTexture:
	texture: Surface
	key: str
	size: Vector2


class TextureClippingCacheModule(GameModule):
	IDMARKER = "texcache"

	_textures = Dict[str, CachedTexture]

	def create(self):
		self._textures = {}

	@staticmethod
	def _make_hash(texture: Surface, size: Vector2):
		return str(hash(texture)) + f"{size[0]}x{size[1]}"

	def get_tex(self, texture: Surface, size: Vector2) -> Optional[CachedTexture]:
		return self._textures.get(self._make_hash(texture, size))

	def contains(self, texture: Surface, size: Vector2):
		return self.get_tex(texture) is not None

	def get_or_insert(self, texture: Surface, size: Vector2) -> Surface:
		if size > Vector2(texture.get_size()):
			raise ValueError(f"Texture size ({Vector2(texture.get_size())}) cannot be less than passed size ({size})")

		tex = self.get_tex(texture, size)
		if tex is not None:
			return tex.texture

		key = self._make_hash(texture, size)
		clipped = surface_region(texture, size)

		self._textures[key] = CachedTexture(clipped, key, size)
		return self._textures[key]




def test_UNIT_texture_clipping():
	pass
