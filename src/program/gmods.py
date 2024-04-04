from gamesystem.mods.modulebase import GameModule
from gameutil import surface_region
from prelude import *


@dataclass
class CachedTexture:
	texture: Surface
	keytext: Surface
	size: Vector2


class TextureClippingCacheModule(GameModule):
	IDMARKER = "textclip"
	_textures: List[CachedTexture]

	def create(self):
		self._textures = []

	def get_tex(self, texture: Surface, size: Vector2) -> Optional[CachedTexture]:
		for entry in self._textures:
			if entry.keytext is texture and size == entry.size:
				return entry
		return None

	def contains(self, texture: Surface, size: Vector2):
		return self.get_tex(texture, size) is not None

	def get_or_insert(self, texture: Surface, size: Vector2) -> Surface:
		if size[0] > texture.get_width() and size[1] > texture.get_height():
			raise ValueError(f"Texture size ({Vector2(texture.get_size())}) cannot be less than passed size ({size})")

		tex = self.get_tex(texture, size)
		if tex is not None:
			return tex.texture

		clipped = surface_region(texture, Rect((0, 0), size))

		self._textures.append(CachedTexture(clipped, texture, size))
		return clipped


class BlueprintsStorageModule(GameModule):
	IDMARKER = "blueprints"

	def create(self, blueprints: Dict[str, Any]):
		if blueprints.get("IDMARKER"):
			del blueprints["IDMARKER"]

		self.cards = SimpleNamespace(**blueprints["cards"])
		self.buildings = SimpleNamespace(**blueprints["buildings"])
		self._blueprints = blueprints

	def icards(self):
		return self.cards.__dict__.items()

	def ibuildings(self):
		return self.buildings.__dict__.items()
