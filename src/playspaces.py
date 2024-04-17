from prelude import *
from gameutil import surface_rounded_corners, shadow_from_rect
from consts import CARD_RECT
from tooltip import Tooltip
from dataclasses import field
import copy
from ui import Dropdown, NamedButton, AbstractButton, Onclick


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
					card = game.cardspawn.get(play_id) if play_id != "random" else game.playerturn.scenario.random_card(exclude=["mixed"])
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
		if card.play_id == "investment":  # special case
			effects = []

		for k, v in self.for_card.items():
			if k == card.play_id:
				effects.extend(v)

		return effects

	def find_any(self, prop, first=True):
		matches = filter(lambda e: e.prop == prop, self.for_any)
		if first:
			return next(matches, None)
		return list(matches)


@dataclass(slots=True)
class Upgrade:
	name: str
	description: str
	effect_type: str
	value: Any
	cost: int
	bought: bool = False

	@classmethod
	def fromjson(cls, j: Dict[str, Any]):
		return cls(**j)

	def can_apply(self, space) -> bool:
		return space.num_investment_tokens() >= self.cost

	def apply(self, space) -> bool:
		if not self.can_apply(space):
			return False

		self.bought = True
		space.add_investment_token(-self.cost)

		# EXTEND UPGRADE EFFECTS HERE
		match self.effect_type:
			case "stamina":
				space.data.stamina += self.value
			case "funds":
				effect = space.data.play_effect.find_any("funds")
				effect.value += self.value
			case "pollution":
				game.playerstate.pollution += self.value
			case "play_effect":
				effect_id, patched = self.value
				effect = space.data.play_effect.find_any(effect_id)
				effect.value = patched
			case "transform":
				space.destroy()
				transformed = Playspace.from_blueprint(game.blueprints.get_building(self.value))
				transformed.rect = space.rect
				game.sprites.new(transformed.with_tooltip())

			case eftype:
				raise ValueError(f"Unknown upgrade effect {eftype}")


@dataclass(slots=True)
class DataPlayspace:
	title: str  # The title of the building
	description: str  # The description of the building
	accept_ids: List[str]  # What card play_id's are accepted by this playspace
	play_effect: PlayEffectInfo  # Which game values are changed when the card is played
	upgrades: List[Upgrade]
	space_id: str  # An identifying string for the building type TODO: Make this an enum
	stamina: int = 3
	# TODO: Add an image property

	@classmethod
	def fromjson(cls, j: Dict[str, str]):
		j["play_effect"] = PlayEffectInfo.fromjson(j.get("play_effect", {}))
		j["upgrades"] = list(map(Upgrade.fromjson, j.get("upgrades", [])))
		return cls(**j)  # type: ignore


class Playspace(Sprite):
	LAYER = "PLAYSPACE"
	DRAGABLE_BAR_HEIGHT = 35
	MAX_DRAG_FRAMES = 10
	DROPDOWN_BUTTON_DIMS = Vector2(30, 50)

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

		dropdown_rect = FRect(VZERO, Playspace.DROPDOWN_BUTTON_DIMS)
		dropdown_pos = self.rect.topright + vec(-dropdown_rect.width*1.2, self.titlebar.height+40)
		self._upgrade_button = Dropdown(dropdown_rect, UpgradeMenu.from_playspace(self).set_pos(dropdown_pos + vec(dropdown_rect.width, 0)))
		self._upgrade_button.rect.topleft = dropdown_pos

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

	def add_investment_token(self, num=1):
		self._investments += num

	def num_investment_tokens(self) -> int:
		return self._investments

	def play_card_onto_space(self, card):
		if card.data.play_id == "investment":
			self.add_investment_token()
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
		return (card.data.play_id in self.data.accept_ids and self._stamina > 0) or (card.data.play_id == "investment" and self._investments < consts.MAX_INVESMENTS)

	def card_hovering(self, card) -> bool:
		return self.rect.colliderect(card.rect.inflate(-card.PLAYABLE_OVERLAP, -card.PLAYABLE_OVERLAP))

	def card_hovering_exclude(self, card) -> bool:
		for space in game.sprites.get("PLAYSPACE"):
			if space.card_hovering(card):
				return space is self
		return False

	# TODO: Fix this for when camera stuff is happening
	def collidecard(self, card) -> bool:
		colliding = self.card_hovering_exclude(card)
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
		self._upgrade_button.update_move()
		self._upgrade_button.rect.topright = self.rect.topright + vec(-6, self.titlebar.height + 40)

		# Should be above other playspaces if it is being dragged or was just dragged
		if self._dragged or self._dragged_frames:
			self.z = 2 * int(self._dragged or self._dragged_frames)
		elif self._upgrade_button.is_down():
			self.z = 1
		else:
			self.z = 0

	def update_draw(self):
		if self._dragged_frames > 0:
			game.windowsystem.screen.blit(self._shadow, self.rect.topleft)

		mo = min(Playspace.MAX_DRAG_FRAMES, self._dragged_frames)
		bpos = self.rect.topleft - Vector2(mo, mo)

		game.windowsystem.screen.blit(self.surface, bpos)

		hover_ofs = Vector2(mo, mo)
		if any(self.card_hovering_exclude(card) for card in game.sprites.get("CARD")):
			game.windowsystem.screen.blit(self._overlay_surface, self.rect.topleft)

			ov_rect = self.rect.copy()
			ov_rect.inflate_ip(-30, -90)

			pygame.draw.line(game.windowsystem.screen, palette.WHITE, ov_rect.topleft, ov_rect.topleft + Vector2(30, 0), 5)
			pygame.draw.line(game.windowsystem.screen, palette.WHITE, ov_rect.topleft, ov_rect.topleft + Vector2(0, 30), 5)

			bot_adj = ov_rect.bottomleft + Vector2(0, 30)
			pygame.draw.line(game.windowsystem.screen, palette.WHITE, bot_adj, bot_adj + Vector2(30, 0), 5)
			pygame.draw.line(game.windowsystem.screen, palette.WHITE, bot_adj, bot_adj + Vector2(0, -30), 5)

			right_adj = ov_rect.bottomright + Vector2(0, 30)
			pygame.draw.line(game.windowsystem.screen, palette.WHITE, right_adj, right_adj + Vector2(-30, 0), 5)
			pygame.draw.line(game.windowsystem.screen, palette.WHITE, right_adj, right_adj + Vector2(0, -30), 5)

		STAM_RAD = 12
		stam_pos = self.rect.topright - hover_ofs
		stam_pos += Vector2(-STAM_RAD * 1.8, 40 + STAM_RAD)

		for i in range(self.data.stamina):
			if i+1 > self._stamina:
				pygame.draw.circle(game.windowsystem.screen, palette.GREY, stam_pos, STAM_RAD, 2)
			else:
				pygame.draw.circle(game.windowsystem.screen, palette.WHITE, stam_pos, STAM_RAD, int(STAM_RAD*0.7))

			stam_pos.x -= STAM_RAD * 3

		self._upgrade_button.rect.topleft -= hover_ofs
		self._upgrade_button.update_draw()

		FUNDS_RAD = 20
		funds_pos = self._upgrade_button.rect.midleft - vec(FUNDS_RAD*1.5, FUNDS_RAD/2)

		for i in range(self._investments):
			pygame.draw.rect(game.windowsystem.screen, palette.WHITE, FRect(funds_pos, (FUNDS_RAD, FUNDS_RAD)), STAM_RAD, border_radius=3)
			funds_pos.x -= FUNDS_RAD * 1.8


class UpgradeButton(NamedButton):
	LAYER = "UI"

	def __init__(self, rect: FRect, upgrade: Upgrade, playspace: Playspace):
		super().__init__(rect, upgrade.name)
		self.space = playspace
		self.upgrade = upgrade

		self._greyout = Surface(self.rect.size, pygame.SRCALPHA)
		self._greyout.fill(palette.BLACK)
		self._greyout.set_alpha(125)
		self._greyout = surface_rounded_corners(self._greyout, 5)

		self._tooltip = Tooltip(self.upgrade.name, self.upgrade.description, self.rect, parent=self)

	def hovered(self) -> bool:
		return super().hovered() and not self.upgrade.bought

	def update_move(self):
		super().update_move()
		self._tooltip.update_move()
		self.z = 5 if self._tooltip.visible() else 0

	def update_draw(self):
		cached_rect = self.rect.copy()
		hovered = self.hovered()
		if self.mouse_down_over():
			self.rect.inflate_ip(-10, -10)
			hovered = False

		pygame.draw.rect(game.windowsystem.screen, self.c, self.rect, border_radius=5)
		pygame.draw.rect(game.windowsystem.screen, palette.GREY, self.rect.inflate(-10, -10), width=2, border_radius=5)

		if hovered:
			pygame.draw.rect(game.windowsystem.screen, palette.GREY, self.rect, width=2, border_radius=5)

		game.windowsystem.screen.blit(self._rendered, self.rect.midleft + Vector2(20, -self._rendered.get_height()/2))

		upgrade_pip_rect = FRect(VZERO, (20, 20))
		upgrade_pip_rect.midright = self.rect.midright - Vector2(20, 0)

		if self.upgrade.bought:
			game.windowsystem.screen.blit(self._greyout, self.rect)
		else:
			clr = Color(255, 0, 0) if not self.upgrade.can_apply(self.space) and self.mouse_down_over() else palette.WHITE
			pygame.draw.rect(game.windowsystem.screen, clr, upgrade_pip_rect, border_radius=5)

			cost_render = self._font.render(str(self.upgrade.cost), True, clr)
			game.windowsystem.screen.blit(cost_render, self.rect.midright - Vector2(50, 0) - Vector2(cost_render.get_size())/2)

		self.rect = cached_rect
		self._tooltip.update_draw()



class UpgradeMenu(Sprite):
	LAYER = "UI"
	PADDING = Vector2(10, 10)
	DEFAULT_BUTTON_SIZE = Vector2(240, 60)

	def __init__(self, rect: FRect, buttons: List[Sprite]):
		self.rect = rect
		self.buttons = buttons

		rectw, recth = UpgradeMenu.PADDING
		rectw += UpgradeMenu.DEFAULT_BUTTON_SIZE.x if not buttons else max(b.rect.width for b in buttons)

		for button in self.buttons:
			recth += button.rect.height
			button.rect.topleft = Vector2(UpgradeMenu.PADDING.x, recth)

		rectw += UpgradeMenu.PADDING.x
		recth += UpgradeMenu.PADDING.y

		self.rect.width = rectw
		self.rect.height = recth

	def set_pos(self, pos: Vector2):
		self.rect.topleft = pos

		anchor = self.rect.topleft + UpgradeMenu.PADDING
		for button in self.buttons:
			button.rect.topleft = anchor
			anchor.y += button.rect.height

		return self

	# TESTING METHOD
	@classmethod
	def from_list(cls, names: List[str]):
		buttons = [NamedButton(FRect(VZERO, cls.DEFAULT_BUTTON_SIZE), name) for name in names]
		rect = FRect(0, 0, 0, 0)
		return cls(rect, buttons)

	@classmethod
	def from_playspace(cls, space: Playspace):
		upgrades = space.data.upgrades
		buttons = [UpgradeButton(FRect(VZERO, cls.DEFAULT_BUTTON_SIZE), upg, space).set_onclick(functools.partial(upg.apply, space)) for upg in upgrades]
		rect = FRect(0, 0, 0, 0)
		return cls(rect, buttons)

	def hovered(self) -> bool:
		return game.input.mouse_within(self.rect)

	def update_move(self):
		for button in self.buttons:
			button.update_move()

	def update_draw(self):
		pygame.draw.rect(game.windowsystem.screen, palette.BLACK, self.rect, border_radius=5)

		for button in sorted(self.buttons, key=lambda btn: btn.z):
			button.update_draw()
