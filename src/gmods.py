from gamesystem.mods.modulebase import GameModule
from gameutil import surface_region
from prelude import *
from cards import Card
from datetime import datetime


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
		self.scenarios = SimpleNamespace(**blueprints["scenarios"])
		self._blueprints = blueprints

	def icards(self) -> Iterator[Tuple[str, dict]]:
		return self.cards.__dict__.items()

	def ibuildings(self) -> Iterator[Tuple[str, dict]]:
		return self.buildings.__dict__.items()

	def iscenarios(self) -> Iterator[Tuple[str, dict]]:
		return self.scenarios.__dict__.items()

	def get_card(self, name):
		return self.cards.__dict__.get(name)

	def get_building(self, name):
		return self.buildings.__dict__.get(name)

	def get_scenario(self, name):
		return self.scenarios.__dict__.get(name)


class CameraSpoofingModule(GameModule):
	IDMARKER = "camera"

	def create(self):
		self.speed = 10

	def update(self):
		vel = 0
		if game.input.key_down(pygame.K_a, pygame.K_LEFT):
			vel += self.speed
		if game.input.key_down(pygame.K_d, pygame.K_RIGHT):
			vel -= self.speed

		for space in game.sprites.get("PLAYSPACE"):
			space.rect.x += vel


class PlayerStateTrackingModule(GameModule):
	IDMARKER = "playerstate"

	def create(self):
		self.reset()

	def reset(self):
		self.pollution = 0.0
		self.funds = 0.1
		self.start_time = datetime.now()

	def time_since_game_start(self):
		return datetime.now() - self.start_time

	def update(self):
		for prop, val in self.__dict__.items():
			if isinstance(val, float):
				self.__dict__[prop] = min(max(0, val), 1.0)

	def incr_property(self, prop, num):
		self.__dict__[prop] += num
		logging.debug(f"PlayerStateTrackingModule: {prop} incremented by {num}. Status: {self}")

	def get_property(self, prop):
		return self.__dict__[prop]

	def has_property(self, prop):
		return prop in self.__dict__


class CardSpawningModule(GameModule):
	IDMARKER = "cardspawn"
	REQUIREMENTS = ["blueprints"]

	def create(self):
		pass

	def random(self, choices: List[str] = []) -> Card:
		choices = [game.blueprints.get_card(card) for card in choices
					] if choices else [v for _, v in game.blueprints.icards()]
		return Card.from_blueprint(random.choice(choices)).with_tooltip()  # type: ignore

	def get(self, play_id: str) -> Card:
		bp = game.blueprints.cards.__dict__.get(play_id)
		return Card.from_blueprint(bp)

	def spawn(self, play_id: str, tooltip=True):
		card = self.get(play_id)
		if tooltip:
			card.with_tooltip()

		game.sprites.new(card)
