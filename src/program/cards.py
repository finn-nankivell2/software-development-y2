from prelude import *
from gameutil import surface_rounded_corners, surface_keepmask, shadow_from_rect, EasingVector2
from particles import particle_explosion, SurfaceParticle
import json
import fonts
from playspaces import Playspace
from tooltip import Tooltip
import logging
import copy


class DespawningCard(Sprite):
	LAYER = "PARTICLE"

	def __init__(self, pos: Vector2, texture: Surface, vel: Vector2 = Vector2(0, -2), lifetime: int = 20):
		self.pos = pos
		self.vel = vel
		self.texture = texture
		self._lifetime = lifetime
		self._opacity = 255
		self._decay = self._opacity / lifetime
		self._easing = EasingVector2(start=self.pos, end=self.pos + self.vel * self._lifetime, duration=self._opacity)

	@classmethod
	def from_card(cls, card, **kwargs):
		return cls(card.rect.topleft, card._surf.copy(), **kwargs)

	def update_move(self):
		self.texture = pygame.transform.scale_by(self.texture, (0.98, 0.98))

		self._opacity -= self._decay

		if self._opacity < 1:
			self.destroy()

	def update_draw(self):
		self.texture.set_alpha(int(self._opacity))
		game.windowsystem.screen.blit(self.texture, self._easing(255 - self._opacity))


class PollutingCard(DespawningCard):

	def __init__(self, pos: Vector2, target: Vector2, texture: Surface, lifetime: int = 20):
		vel = (target - pos) / lifetime
		super().__init__(pos, texture, vel, lifetime)

	@classmethod
	def from_card(cls, card, target, **kwargs):
		return cls(card.rect.topleft, target, card._surf, **kwargs)

	def update_draw(self):
		game.windowsystem.screen.blit(self.texture, self._easing(255 - self._opacity))


@dataclass(slots=True)
class DataCard:
	title: str  # The title of the card
	description: str  # The description of the card
	playable_everywhere: bool  # Whether the card can be played onto empty space as well as playspaces
	play_id: str
	# TODO: Add an image property

	@classmethod
	def fromjson(cls, j: Dict[str, str]):
		j = copy.deepcopy(j)
		return cls(**j)  # type: ignore


class Card(Sprite):
	LAYER = "CARD"
	PICKME_SHIFT_AMT = 50
	SHADOW_OFFSET = 10
	PLAYABLE_OVERLAP = 100

	def __init__(self, rect: FRect, texture: Surface, data: DataCard):
		self.rect = FRect(rect)
		self.hand_locked = False  # If card is drifting towards or in hand
		self.dragged = False  # If card is currently held by the mouse
		self.mouse_offset = Vector2(0, 0)  # Point where the mouse grabbed the card
		self.held_frames = 0  # How many frames card has been held for
		self.data = data

		clipped = game.textclip.get_or_insert(texture, self.rect.size)
		self._setup_surfaces(clipped)

	@classmethod
	def from_blueprint(cls, blueprint: Dict[str, Any]):
		data = DataCard.fromjson(blueprint["data"])
		texture = game.assets.get(blueprint["texture"])
		return cls(consts.CARD_RECT, texture, data)

	def with_tooltip(self):
		game.sprites.new(Tooltip(self.data.title, self.data.description, self.rect, parent=self))
		return self

	def _setup_surfaces(self, texture: Surface):
		self._surf = Surface(self.rect.size, pygame.SRCALPHA)
		self._shadow_surf = self._surf.copy()

		r = self.rect.copy()
		r.topleft = VZERO  # type: ignore

		self._surf.blit(texture, VZERO)
		self._surf = surface_rounded_corners(texture, 5)

		pygame.draw.rect(self._surf, palette.BLACK, r, border_radius=5, width=10)

		heading_bg = r.inflate(-30, -r.height * 0.85)
		heading_bg.y = 0

		pygame.draw.rect(self._surf, palette.GREY, r.inflate(-10, -10), border_radius=5, width=2)
		pygame.draw.rect(self._surf, palette.BLACK, heading_bg, border_radius=10)

		title_surf = fonts.families.roboto.size(18).render(self.data.title, True, palette.WHITE)
		self._surf.blit(title_surf, heading_bg.center - Vector2(title_surf.get_size()) / 2)

		self._shadow_surf = shadow_from_rect(self._surf.get_rect(), border_radius=5)

	def playspace_collide(self) -> Optional[Playspace]:
		for playspace in game.sprites.get("PLAYSPACE"):
			if playspace.collidecard(self):
				return playspace

		return None

	def is_playable(self) -> bool:
		return self.playspace_collide() is not None

	def is_hovered(self) -> bool:
		return any(space.card_hovering_exclude(self) for space in game.sprites.get("PLAYSPACE"))

	def mouse_over_me(self) -> bool:
		return self.rect.collidepoint(game.input.mouse_pos())

	def update_move(self):
		hand = game.sprites.HAND
		rep = hand.get_card_rep(self)
		if rep and rep.idx > consts.HAND_SIZE:
			self.destroy()
			logging.info(f"Destroyed card because of hand limit with idx: {rep.idx} with data: {self.data}")

		if game.input.mouse_pressed(0) and hand.currently_dragged is None:
			if self.mouse_over_me() and not self.dragged:
				self.dragged = True
				self.hand_locked = False
				self.mouse_offset = game.input.mouse_pos() - self.rect.topleft
				hand.currently_dragged = self

		if not game.input.mouse_down(0) and self.dragged:
			self.dragged = False
			space = self.playspace_collide()
			if space:
				space.play_card_onto_space(self)
				self.destroy_anim()

		# Logic for if the Card is being dragged
		if self.dragged:
			self.rect.topleft = game.input.mouse_pos() - self.mouse_offset
			self.held_frames += 1
			if self.held_frames < Card.SHADOW_OFFSET:
				self.mouse_offset += Vector2(1, 1)
		else:
			self.hand_locked = True
			if self.held_frames > Card.SHADOW_OFFSET:
				self.held_frames = Card.SHADOW_OFFSET
			elif self.held_frames > 0:
				self.held_frames -= 1

			if hand.currently_dragged is self:
				hand.currently_dragged = None

		if self.hand_locked:
			target = hand.get_position_from_card(self)
			if target:
				if self.mouse_over_me() and hand.currently_dragged is None:
					target -= Vector2(0, Card.PICKME_SHIFT_AMT)

				travel = target - self.rect.bottomleft
				self.rect.bottomleft += travel / 10

				if travel.length() < 1:
					self.rect.bottomleft = target
				else:
					self.z = 1

	def destroy(self):
		super().destroy()
		logging.debug(f"Destroyed card: {self.data}")

	def destroy_anim(self, **kwargs):
		self.destroy()
		game.sprites.new(DespawningCard.from_card(self, **kwargs))

	def destroy_into_polluting(self, target=None, **kwargs):
		self.destroy()
		target = target if target else Vector2(game.windowsystem.rect.topright)
		game.sprites.new(PollutingCard.from_card(self, target=target, **kwargs))

	def update_draw(self):
		if self.held_frames:
			shadow_rect = Vector2(self.rect.topleft)
			shadow_rect += Vector2(1, 1) * min(Card.SHADOW_OFFSET, self.held_frames)
			game.windowsystem.screen.blit(self._shadow_surf, shadow_rect)

		game.windowsystem.screen.blit(self._surf, self.rect.topleft)


class FollowMouse(Sprite):
	LAYER = "UI"

	def __init__(self):
		self.pos = Vector2(0, 0)

	def update_move(self):
		self.pos = game.input.mouse_pos()

	def update_draw(self):
		pygame.draw.circle(game.windowsystem.screen, Color("#ffffff11"), self.pos, 50)


class Hand(Sprite):
	LAYER = "MANAGER"

	CARD_SPACING = 20

	@dataclass
	class CardRep:
		card: Card
		idx: int

	def __init__(self, rect):
		self.rect = rect
		self.currently_dragged = None
		self.card_map = []

	def contains(self, card):
		"""Check if Card is contained in CardRef list"""
		return self.get_card_rep(card) is not None

	def update_move(self):
		cglobal = game.sprites.get("CARD")
		for card in cglobal:
			if self.get_card_rep(card) is None:
				self.card_map.append(Hand.CardRep(card, len(self.card_map) - 1))

		self.card_map = [ref for ref in self.card_map if not ref.card.is_destroyed()]

		idxs = [ref.idx for ref in self.card_map]
		self.card_map.sort(key=lambda ref: ref.card.rect.x)

		if self.currently_dragged is not None and not self.currently_dragged.is_playable() and idxs != [
			ref.idx for ref in self.card_map
		]:
			game.audio.sounds.card_switch.play()

		for i, ref in enumerate(self.card_map):
			ref.idx = i
			ref.card.z = 0

		if self.currently_dragged:
			self.currently_dragged.z = 2


	def get_position_from_card(self, card) -> Optional[Vector2]:
		total_width = sum(
			ref.card.rect.width + Hand.CARD_SPACING if not ref.card.is_playable() else 0 for ref in self.card_map
		)

		start_pos = self.rect.midbottom - Vector2(total_width / 2, 0)
		for ref in sorted(self.card_map, key=lambda ref: ref.idx):
			if card is ref.card:
				return start_pos
			if not ref.card.is_playable():
				start_pos += Vector2(card.rect.width + Hand.CARD_SPACING, 0)

		return None

	def get_position_from_ref(self, ref) -> Optional[Vector2]:
		return self.get_position_from_card(ref.card)

	def get_card_rep(self, card):
		"""Get CardRep from Card"""
		for rep in self.card_map:
			if rep.card is card:
				return rep
		return None
