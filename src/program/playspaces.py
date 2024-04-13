from prelude import *
from gameutil import surface_rounded_corners, shadow_from_rect
from consts import CARD_RECT
from tooltip import Tooltip
from dataclasses import field
import copy


@dataclass(slots=True)
class Effect:
	prop: str
	value: float

	@classmethod
	def fromtuple(cls, items):
		return cls(*items)

	def _special_case(self):
		match self.prop:
			case "dealcards":
				for play_id in self.value:
					card = game.cardspawn.get(play_id) if play_id != "random" else game.cardspawn.random()
					game.sprites.new(card)

			case _:
				raise Exception(f"rule {self.prop} with values {self.value} is invalid")

	def apply(self):
		if game.playerstate.has_property(self.prop):
			game.playerstate.incr_property(self.prop, self.value)
		else:
			self._special_case()


@dataclass(slots=True)
class PlayEffectInfo:
	for_any: List[Effect] = field(default_factory=list)
	for_card: Dict[str, List[Effect]] = field(default_factory=dict)

	@classmethod
	def fromjson(cls, j):
		for_any = list(map(Effect.fromtuple, j.get("for_any", {}).items()))
		for_card = {
			play_id: list(map(Effect.fromtuple, effects.items())) for play_id, effects in j.get("for_card", {}).items()
		}

		return cls(for_any, for_card)

	def get_applicable(self, card) -> List[Effect]:
		effects = self.for_any.copy()
		for k, v in self.for_card.items():
			if k == card.play_id:
				effects.extend(v)

		return effects


@dataclass(slots=True)
class DataPlayspace:
	title: str  # The title of the building
	description: str  # The description of the building
	accept_ids: List[str]  # What card play_id's are accepted by this playspace
	play_effect: PlayEffectInfo  # Which game values are changed when the card is played
	space_id: str  # An identifying string for the building type TODO: Make this an enum
	stamina: int = 3
	# TODO: Add an image property

	@classmethod
	def fromjson(cls, j: Dict[str, str]):
		j["play_effect"] = PlayEffectInfo.fromjson(j.get("play_effect", {}))
		return cls(**j)  # type: ignore


class Playspace(Sprite):
	LAYER = "PLAYSPACE"
	DRAGABLE_BAR_HEIGHT = 35
	MAX_DRAG_FRAMES = 10

	def __init__(self, rect, surface, data):
		self.rect = rect
		self.data = data

		self.titlebar = self.rect.copy()
		self.titlebar.height = Playspace.DRAGABLE_BAR_HEIGHT
		self._dragged = False
		self._drag_offset = Vector2(0, 0)
		self._dragged_frames = 0
		self._dragged_poe = None

		texture = surface.copy()
		titlesurf = Surface(self.titlebar.size, pygame.SRCALPHA)
		titlesurf.fill(palette.BLACK)
		texture.blit(titlesurf, VZERO)

		self.surface = game.textclip.get_or_insert(texture, rect.size)
		self.surface = surface_rounded_corners(self.surface, 5)
		pygame.draw.rect(self.surface, palette.BLACK, Rect(VZERO, self.rect.size), width=5, border_radius=5)

		self._overlay_surface = Surface(rect.size, pygame.SRCALPHA)
		self._overlay_surface.fill(palette.BLACK)
		self._overlay_surface = surface_rounded_corners(self._overlay_surface, 5)
		self._overlay_surface.set_alpha(127)

		self._shadow = shadow_from_rect(self.surface.get_rect(), border_radius=5)
		self._investments = 0
		self._stamina = self.data.stamina

	@classmethod
	def from_blueprint(cls, blueprint):
		blueprint = copy.deepcopy(blueprint)
		data = DataPlayspace.fromjson(blueprint["data"])
		texture = game.assets.get(blueprint["texture"])

		dest = Playspace._find_availible_space(consts.BUILDING_RECT.copy())
		ret = cls(dest, texture, data)
		ret._picture = blueprint["texture"]

		return ret

	@staticmethod
	def _find_availible_space(rect):

		def check():
			return any(space.rect.colliderect(rect) for space in game.sprites.get("PLAYSPACE"))

		while check() and rect.right < game.windowsystem.dimensions.x:
			rect.x += consts.CARD_RECT.width * 1.1

		if rect.right >= game.windowsystem.dimensions.x:
			rect.x = consts.BUILDING_RECT.x
			rect.y += consts.CARD_RECT.height * 1.1
			return Playspace._find_availible_space(rect)

		return rect

	def with_tooltip(self):
		game.sprites.new(Tooltip(self.data.title, self.data.description, self.rect, parent=self))
		return self

	def add_investment_token(self):
		self._investments += 1

	def play_card_onto_space(self, card):
		if card.data.play_id == "investment":
			# special logic
			pass
		else:
			self._stamina -= 1
			for effect in self.data.play_effect.get_applicable(card.data):
				effect.apply()

	def refill_stamina(self):
		self._stamina = self.data.stamina

	def is_dragged(self) -> bool:
		return self._dragged

	def _permission_to_drag(self) -> bool:
		return not any(space.is_dragged() for space in game.sprites.get("PLAYSPACE") if space is not self)

	def card_validation(self, card) -> bool:
		return card.data.play_id in self.data.accept_ids and self._stamina > 0

	def card_hovering(self, card) -> bool:
		return self.rect.colliderect(card.rect.inflate(-card.PLAYABLE_OVERLAP, -card.PLAYABLE_OVERLAP))

	def card_hovering_exclude(self, card) -> bool:
		for space in game.sprites.get("PLAYSPACE"):
			if space.card_hovering(card):
				return space is self
		return False

	# TODO: Fix this for when camera stuff is happening
	def collidecard(self, card) -> bool:
		colliding = self.card_hovering(card)
		playable = self.card_validation(card)
		return colliding and playable and not self._dragged

	def _invalid_placement(self) -> bool:
		"""Returns True if placement is invalid, playspace will return to initial position before dragging begun"""
		return any(
			self.collidecard(card) for card in game.sprites.get("CARD")
		) or self.rect.bottom > game.windowsystem.dimensions.y - CARD_RECT.height or any(
			self.rect.colliderect(space.rect) for space in game.sprites.get("PLAYSPACE") if space is not self
		) or self.rect.clamp(game.windowsystem.rect) != self.rect

	def _drop_drag(self):
		self._dragged = False
		if self._invalid_placement():
			pass
		else:
			self._dragged_poe = None

	def _check_for_drag(self) -> bool:
		return game.input.mouse_pressed(0) and game.input.mouse_within(self.titlebar) and self._permission_to_drag()

	def update_move(self):
		if self._check_for_drag():
			self._dragged = True
			self._drag_offset = game.input.mouse_pos() - self.titlebar.topleft
			self._dragged_poe = self.titlebar.topleft

		if self._dragged:
			self._dragged_frames += 1
			target = game.input.mouse_pos() - self._drag_offset
			self.rect.topleft = target

			if not game.input.mouse_down(0):
				self._drop_drag()

		else:
			if self._dragged_poe is not None:
				mv = (Vector2(self.rect.topleft) - self._dragged_poe) / 10
				self.rect.topleft -= mv
				if mv.magnitude() < 0.1:
					self.rect.topleft = self._dragged_poe
					self._dragged_poe = None

			if self._dragged_frames > 0:
				self._dragged_frames -= 1

		if self._dragged_frames > Playspace.MAX_DRAG_FRAMES:
			self._dragged_frames = Playspace.MAX_DRAG_FRAMES

		self.titlebar.topleft = self.rect.topleft

		# Should be above other playspaces if it is being dragged or was just dragged
		self.z = int(self._dragged or self._dragged_frames)

	def update_draw(self):
		if self._dragged_frames > 0:
			game.windowsystem.screen.blit(self._shadow, self.rect.topleft)

		mo = min(Playspace.MAX_DRAG_FRAMES, self._dragged_frames)
		bpos = self.rect.topleft - Vector2(mo, mo)

		game.windowsystem.screen.blit(self.surface, bpos)

		if any(self.card_hovering_exclude(card) for card in game.sprites.get("CARD")):
			game.windowsystem.screen.blit(self._overlay_surface, self.rect.topleft)

			ov_rect = self.rect.copy()
			ov_rect.inflate_ip(-30, -90)

			pygame.draw.line(game.windowsystem.screen, palette.WHITE, ov_rect.topleft, Vector2(ov_rect.topleft) + Vector2(30, 0), 5)
			pygame.draw.line(game.windowsystem.screen, palette.WHITE, ov_rect.topleft, Vector2(ov_rect.topleft) + Vector2(0, 30), 5)

			bot_adj = Vector2(ov_rect.bottomleft) + Vector2(0, 30)
			pygame.draw.line(game.windowsystem.screen, palette.WHITE, bot_adj, bot_adj + Vector2(30, 0), 5)
			pygame.draw.line(game.windowsystem.screen, palette.WHITE, bot_adj, bot_adj + Vector2(0, -30), 5)

			right_adj = Vector2(ov_rect.bottomright) + Vector2(0, 30)
			pygame.draw.line(game.windowsystem.screen, palette.WHITE, right_adj, right_adj + Vector2(-30, 0), 5)
			pygame.draw.line(game.windowsystem.screen, palette.WHITE, right_adj, right_adj + Vector2(0, -30), 5)

		STAM_RAD = 12
		stam_pos = self.rect.topright - Vector2(mo, mo)
		stam_pos += Vector2(-STAM_RAD * 1.8, 40 + STAM_RAD)

		for _ in range(self._stamina):
			pygame.draw.circle(game.windowsystem.screen, palette.WHITE, stam_pos, STAM_RAD, int(STAM_RAD*0.7))
			stam_pos.x -= STAM_RAD * 3
