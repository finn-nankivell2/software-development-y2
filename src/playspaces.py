from prelude import *
from gameutil import surface_rounded_corners, shadow_from_rect
from consts import CARD_RECT
from tooltip import Tooltip
from dataclasses import field
import copy
from ui import Dropdown, NamedButton, AbstractButton, Onclick
from particles import DeflatingParticle


# An Effect that is triggered when a Card is played to a Playspace
@dataclass(slots=True)
class Effect:
	prop: str
	value: float

	@classmethod
	def fromtuple(cls, items):
		return cls(*items)

	# In some cases, code needs to be run when a card is played
	def _special_case(self):
		match self.prop:
			# If the type of effect is dealcards, then deal the cards defined by the Effect's value
			case "dealcards":
				for play_id in self.value:
					card = game.cardspawn.get(play_id) if play_id != "random" else game.playerturn.scenario.random_card(
						exclude=["mixed"]
					)
					game.sprites.new(card)

			# If the case is unknown raise an Exception. Remove during production
			# case _:
			# 	raise Exception(f"rule {self.prop} with values {self.value} is invalid")

	# Apply the effect to the games playerstate module, or run special case code if the effect is a special case
	def apply(self):
		if game.playerstate.has_property(self.prop):
			game.playerstate.incr_property(self.prop, self.value)
		else:
			self._special_case()


# Collection of different Effects for different effect types and card triggers
@dataclass(slots=True)
class PlayEffectInfo:
	# Effects that trigger when any card is played
	for_any: List[Effect] = field(default_factory=list)

	# Effects that only trigger when specific cards are played
	for_card: Dict[str, List[Effect]] = field(default_factory=dict)

	@classmethod
	def fromjson(cls, j):
		for_any = list(map(Effect.fromtuple, j.get("for_any", {}).items()))
		for_card = {
			play_id: list(map(Effect.fromtuple, effects.items())) for play_id, effects in j.get("for_card", {}).items()
		}

		return cls(for_any, for_card)

	# Return the list of effects to be triggered for the given card type
	def get_applicable(self, card) -> List[Effect]:
		effects = self.for_any.copy()
		if card.play_id == "investment":  # special case
			effects = []

		for k, v in self.for_card.items():
			if k == card.play_id:
				effects.extend(v)

		return effects

	# Find a play effect with the given property
	def find_any(self, prop, first=True):
		matches = filter(lambda e: e.prop == prop, self.for_any)
		if first:
			return next(matches, None)
		return list(matches)


# Dataclass representing an upgrade that can be applied to a Playspace, increasing its capabilities
@dataclass(slots=True)
class Upgrade:
	name: str  # The name of the upgrade
	description: str  # A description of the upgrade for the player
	effect_type: str  # The type of upgrade effect to apply
	value: Any  # The upgrade vaue to apply (can be any type)
	cost: int  # The cost in upgrade points
	bought: bool = False  # If the upgrade has been bought
	persist: bool = False  # If the upgrade can be bought multiple times

	@classmethod
	def fromjson(cls, j: Dict[str, Any]):
		return cls(**j)

	# If there are enough upgrade points on the given Playspace to afford the upgrade
	def can_apply(self, space) -> bool:
		return space.num_investment_tokens() >= self.cost

	# Apply the upgrade to a given Playspace
	def apply(self, space) -> bool:
		if not self.can_apply(space):
			return False

		self.bought = True and not self.persist
		space.add_investment_token(-self.cost)

		# Check for the correct upgrade type and apply the corresponding logic
		match self.effect_type:
			case "stamina":
				space.data.stamina += self.value
				space._stamina += self.value
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
				game.sprites.new(DeflatingParticle(transformed.rect.inflate(40, 40), palette.GREY), layer_override="LOWPARTICLE")
				game.sprites.new(transformed.with_tooltip())

			case eftype:
				raise ValueError(f"Unknown upgrade effect {eftype}")


# Dataclass representing of a Playspace. Encapsulates all its Effects, Upgrades, and other data points
@dataclass(slots=True)
class DataPlayspace:
	title: str  # The title of the building
	description: str  # The description of the building
	accept_ids: List[str]  # What card play_id's are accepted by this playspace
	play_effect: PlayEffectInfo  # Which game values are changed when the card is played
	upgrades: List[Upgrade]  # List of upgrades for this building
	space_id: str  # An identifying string for the building type
	stamina: int = 3  # How many cards can be played to this Playspace per turn (default is 3)
	construction_cost: int = 1  # How many investments it costs to construct this Playspace (default is 1, used if no json data is given)

	@classmethod
	def fromjson(cls, j: Dict[str, str]):
		j = j.copy()
		j["play_effect"] = PlayEffectInfo.fromjson(j.get("play_effect", {}))
		j["upgrades"] = list(map(Upgrade.fromjson, j.get("upgrades", [])))
		return cls(**j)  # type: ignore


# Gameobject for Playspace
class Playspace(Sprite):
	LAYER = "PLAYSPACE"
	DRAGABLE_BAR_HEIGHT = 35
	MAX_DRAG_FRAMES = 10
	DROPDOWN_BUTTON_DIMS = Vector2(30, 50)

	def __init__(self, rect, surface, data):
		self.rect = rect
		self.data = data

		# Speical case where the Consntruction type's upgrades need to match the availible buildings for the current scenario
		if self.data.space_id == "construction":
			upgrades = []
			for space_id in game.playerturn.scenario.buildable_buildings:
				space_data = DataPlayspace.fromjson(game.blueprints.get_building(space_id)["data"])
				upgrades.append(
					Upgrade(
						space_data.title, space_data.description, "transform", space_id, space_data.construction_cost
					)
				)

			self.data.upgrades = upgrades

		# Special case where the Playspace is a wincondition, which means by constructing it the player has won the game
		elif self.data.space_id == "wincondition":
			game.playerturn.you_win()

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

		# Create the Playspace's Surface that will be used to render it
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
		dropdown_pos = self.rect.topright + vec(-dropdown_rect.width * 1.2, self.titlebar.height + 40)
		self._upgrade_button = Dropdown(
			dropdown_rect, UpgradeMenu.from_playspace(self).set_pos(dropdown_pos + vec(dropdown_rect.width, 0))
		)
		self._upgrade_button.rect.topleft = dropdown_pos

	# Create a Playspace based on json data
	@classmethod
	def from_blueprint(cls, blueprint):
		blueprint = copy.deepcopy(blueprint)
		data = DataPlayspace.fromjson(blueprint["data"])
		texture = game.assets.get(blueprint["texture"])

		dest = Playspace._find_availible_space(consts.BUILDING_RECT.copy())
		ret = cls(dest, texture, data)
		ret._picture = blueprint["texture"]

		return ret

	# Find empty space on the screen where the Playspace can be placed
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

	# Spawn an accompanying tooltip for the Playspace
	def with_tooltip(self):
		game.sprites.new(Tooltip(self.data.title, self.data.description, self.rect, parent=self))
		return self

	# Add an upgrade point to the Playspace
	def add_investment_token(self, num=1):
		self._investments += num

	# Get the number of upgrade points
	def num_investment_tokens(self) -> int:
		return self._investments

	# Play a card onto this playspace and trigger all the effects that come with that
	def play_card_onto_space(self, card):
		# If the card was an investment, then add an upgrade point
		if card.data.play_id == "investment":
			self.add_investment_token()
		else:
			game.audio.sounds.dispose.play()
			self._stamina -= 1

		# Trigger the applicable effects
		for effect in self.data.play_effect.get_applicable(card.data):
			effect.apply()

	# Reset the Playspace stamina to full
	def refill_stamina(self):
		self._stamina = self.data.stamina

	# Is the Playspace currently dragged by the player
	def is_dragged(self) -> bool:
		return self._dragged

	# Can the Playspace start being dragged (only one Playspace can be dragged at once)
	def _permission_to_drag(self) -> bool:
		return not any(space.is_dragged() for space in game.sprites.get("PLAYSPACE") if space is not self)

	# Is the card to be played to the Playspace valid and will it be accepted
	def card_validation(self, card) -> bool:
		return (card.data.play_id in self.data.accept_ids and
				self._stamina > 0) or (card.data.play_id == "investment" and self._investments < consts.MAX_INVESMENTS)

	# Is there a card hovering above the Playspace this frame
	def card_hovering(self, card) -> bool:
		return self.rect.colliderect(card.rect.inflate(-card.PLAYABLE_OVERLAP, -card.PLAYABLE_OVERLAP))

	# Is there a card hovering above this Playspace exclusively
	def card_hovering_exclude(self, card) -> bool:
		for space in game.sprites.get("PLAYSPACE"):
			if space.card_hovering(card):
				return space is self
		return False

	# Collide with a given card to see if it is within play range, and will also be accepted
	def collidecard(self, card) -> bool:
		colliding = self.card_hovering_exclude(card)
		playable = self.card_validation(card)
		return colliding and playable and not self._dragged

	# If the Playspace is dragged somewhere invalid and dropped. Returns True if placement is invalid, playspace will return to initial position before dragging begun
	def _invalid_placement(self) -> bool:
		return any(
			self.collidecard(card) for card in game.sprites.get("CARD")
		) or self.rect.bottom > game.windowsystem.dimensions.y - CARD_RECT.height or any(
			self.rect.colliderect(space.rect) for space in game.sprites.get("PLAYSPACE") if space is not self
		) or self.rect.y < 0

	def _drop_drag(self):
		self._dragged = False
		if not self._invalid_placement():
			self._dragged_poe = None

	# If the Playspace's titlebar is being clicked on by the mouse this frame
	def _check_for_drag(self) -> bool:
		return game.input.mouse_pressed(0) and game.input.mouse_within(self.titlebar) and self._permission_to_drag()

	# Update physical inernals
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

	# Render the Playspace
	def update_draw(self):
		if self._dragged_frames > 0:
			game.windowsystem.screen.blit(self._shadow, self.rect.topleft)

		# When the Playspace is dragged, a animation plays where it jumps off of the background slightly. This vector determines the offset that creates that animation
		mo = min(Playspace.MAX_DRAG_FRAMES, self._dragged_frames)
		hover_ofs = Vector2(mo, mo)

		bpos = self.rect.topleft - hover_ofs
		game.windowsystem.screen.blit(self.surface, bpos)

		# Draw an overaly on top of the Playspace if a card is hovering it exclusively
		if any(self.card_hovering_exclude(card) for card in game.sprites.get("CARD")):
			game.windowsystem.screen.blit(self._overlay_surface, self.rect.topleft)

			ov_rect = self.rect.copy()
			ov_rect.inflate_ip(-30, -90)

			pygame.draw.line(
				game.windowsystem.screen, palette.WHITE, ov_rect.topleft, ov_rect.topleft + Vector2(30, 0), 5
			)
			pygame.draw.line(
				game.windowsystem.screen, palette.WHITE, ov_rect.topleft, ov_rect.topleft + Vector2(0, 30), 5
			)

			bot_adj = ov_rect.bottomleft + Vector2(0, 30)
			pygame.draw.line(game.windowsystem.screen, palette.WHITE, bot_adj, bot_adj + Vector2(30, 0), 5)
			pygame.draw.line(game.windowsystem.screen, palette.WHITE, bot_adj, bot_adj + Vector2(0, -30), 5)

			right_adj = ov_rect.bottomright + Vector2(0, 30)
			pygame.draw.line(game.windowsystem.screen, palette.WHITE, right_adj, right_adj + Vector2(-30, 0), 5)
			pygame.draw.line(game.windowsystem.screen, palette.WHITE, right_adj, right_adj + Vector2(0, -30), 5)

		STAM_RAD = 12
		stam_pos = self.rect.topright - hover_ofs
		stam_pos += Vector2(-STAM_RAD * 1.8, 40 + STAM_RAD)

		# Render the ui for the stamina pips
		for i in range(self.data.stamina):
			if i + 1 > self._stamina:
				pygame.draw.circle(game.windowsystem.screen, palette.GREY, stam_pos, STAM_RAD, 2)
			else:
				pygame.draw.circle(game.windowsystem.screen, palette.WHITE, stam_pos, STAM_RAD, int(STAM_RAD * 0.7))

			stam_pos.x -= STAM_RAD * 3

		self._upgrade_button.rect.topleft -= hover_ofs
		self._upgrade_button.update_draw()

		FUNDS_RAD = 20
		funds_pos = self._upgrade_button.rect.midleft - vec(FUNDS_RAD * 1.5, FUNDS_RAD / 2)

		# Render the ui for the upgrade points
		for i in range(self._investments):
			pygame.draw.rect(
				game.windowsystem.screen,
				palette.WHITE,
				FRect(funds_pos, (FUNDS_RAD, FUNDS_RAD)),
				STAM_RAD,
				border_radius=3
			)
			funds_pos.x -= FUNDS_RAD * 1.8


# Button for upgrading a Playspace
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

		# Tooltip describing the upgrade
		self._tooltip = Tooltip(self.upgrade.name, self.upgrade.description, self.rect, parent=self)

	# Should be be hoverable if the upgrade has been bought
	def hovered(self) -> bool:
		return super().hovered() and not self.upgrade.bought

	def update_move(self):
		super().update_move()
		self._tooltip.update_move()
		self.z = 5 if self._tooltip.visible() else 0

	# Render the upgrade button, including name and cost
	def update_draw(self):
		rect = self.rect.copy()
		hovered = self.hovered()
		if self.mouse_down_over():
			rect.inflate_ip(-10, -10)
			hovered = False

		pygame.draw.rect(game.windowsystem.screen, self.c, rect, border_radius=5)
		pygame.draw.rect(game.windowsystem.screen, palette.GREY, rect.inflate(-10, -10), width=2, border_radius=5)

		if hovered:
			pygame.draw.rect(game.windowsystem.screen, palette.GREY, rect, width=2, border_radius=5)

		game.windowsystem.screen.blit(self._rendered, rect.midleft + Vector2(20, -self._rendered.get_height() / 2))

		upgrade_pip_rect = FRect(VZERO, (20, 20))
		upgrade_pip_rect.midright = rect.midright - Vector2(20, 0)

		if self.upgrade.bought:
			game.windowsystem.screen.blit(self._greyout, rect)
		else:
			clr = Color(255, 0,
						0) if not self.upgrade.can_apply(self.space) and self.mouse_down_over() else palette.WHITE
			pygame.draw.rect(game.windowsystem.screen, clr, upgrade_pip_rect, border_radius=5)

			cost_render = self._font.render(str(self.upgrade.cost), True, clr)
			game.windowsystem.screen.blit(
				cost_render, rect.midright - Vector2(50, 0) - Vector2(cost_render.get_size()) / 2
			)

		self._tooltip.update_draw()


# Menu containing a list of upgrades and UpgradeButtons
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

	# TESTING METHOD, not for use in production
	@classmethod
	def from_list(cls, names: List[str]):
		buttons = [NamedButton(FRect(VZERO, cls.DEFAULT_BUTTON_SIZE), name) for name in names]
		rect = FRect(0, 0, 0, 0)
		return cls(rect, buttons)

	# Generates UpgradeMenu from a Playspace's data
	@classmethod
	def from_playspace(cls, space: Playspace):
		upgrades = space.data.upgrades
		buttons = [
			UpgradeButton(FRect(VZERO, cls.DEFAULT_BUTTON_SIZE), upg,
							space).set_onclick(functools.partial(upg.apply, space)) for upg in upgrades
		]
		rect = FRect(0, 0, 0, 0)
		return cls(rect, buttons)

	def hovered(self) -> bool:
		return game.input.mouse_within(self.rect)

	def update_move(self):
		for button in self.buttons:
			button.update_move()

	# Draw background and button list
	def update_draw(self):
		pygame.draw.rect(game.windowsystem.screen, palette.BLACK, self.rect, border_radius=5)

		for button in sorted(self.buttons, key=lambda btn: btn.z):
			button.update_draw()
