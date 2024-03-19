from gamesystem import game
import pygame
from pygame import Vector2, FRect, Color, Surface
from gamesystem.common.sprite import Sprite
from dataclasses import dataclass
from typing import Optional, Dict
from gameutil import surface_rounded_corners
from consts import VZERO
from particles import particle_explosion
import json
import fonts


class DebugRect():

	def update_draw(self):
		pygame.draw.rect(game.windowsystem.screen, Color("#ff00ff"), self.rect)


class Playspace(DebugRect, Sprite):
	LAYER = "PLAYSPACE"

	def __init__(self, rect, colour):
		self.rect = rect
		self.colour = colour

	def update_draw(self):
		pygame.draw.rect(game.windowsystem.screen, self.colour, self.rect, border_radius=5)


class Playspace2(Playspace):
	def __init__(self, rect, surface):
		self.rect = rect
		self.surface = game.textclip.get_or_insert(surface, rect.size)
		self.surface = surface_rounded_corners(self.surface, 5)

	def update_draw(self):
		game.windowsystem.screen.blit(self.surface, self.rect.topleft)



@dataclass(slots=True, frozen=True)
class DataCard:
	title: str
	description: str
	play_condition: str # TODO: Make this an enum
	play_id: str # TODO: And this too

	@classmethod
	def fromjson(cls, j: Dict[str, str]):
		return DataCard(**j)


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

	def _setup_surfaces(self, texture: Surface):
		self._surf = Surface(self.rect.size, pygame.SRCALPHA)
		self._shadow_surf = self._surf.copy()

		r = self.rect.copy()
		r.topleft = VZERO  # type: ignore

		self._surf.blit(texture, VZERO)
		self._surf = surface_rounded_corners(texture, 5)

		pygame.draw.rect(self._surf, Color("#000000"), r, border_radius=5, width=10)

		heading_bg = r.inflate(-30, -r.height * 0.85)
		heading_bg.y = 0

		pygame.draw.rect(self._surf, Color("#959595"), r.inflate(-10, -10), border_radius=5, width=2)
		pygame.draw.rect(self._surf, Color("#000000"), heading_bg, border_radius=10)

		title_surf = fonts.NONE_FONT.render(self.data.title, True, Color("#ffffff"))
		self._surf.blit(title_surf, r.midtop - Vector2(title_surf.get_width()/2, -10))


		pygame.draw.rect(self._shadow_surf, Color("#000000aa"), r.inflate(-10, -10), border_radius=5)
		self._shadow_surf = pygame.transform.gaussian_blur(self._shadow_surf, 8)

	def playspace_collide(self) -> Optional[Playspace]:
		for playspace in game.sprites.get("PLAYSPACE"):
			if playspace.rect.colliderect(self.rect.inflate(-Card.PLAYABLE_OVERLAP, -Card.PLAYABLE_OVERLAP)):
				return playspace

		return None

	def is_playable(self) -> bool:
		return self.playspace_collide() is not None

	def mouse_over_me(self) -> bool:
		return self.rect.collidepoint(game.input.mouse_pos())

	def update_move(self):
		hand = game.sprites.HAND

		if game.input.mouse_pressed(0) and hand.currently_dragged is None:
			if self.mouse_over_me() and not self.dragged:
				self.dragged = True
				self.hand_locked = False
				self.mouse_offset = game.input.mouse_pos() - self.rect.topleft
				hand.currently_dragged = self

		if not game.input.mouse_down(0) and self.dragged:
			self.dragged = False
			if self.is_playable():
				self.destroy()

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
		game.sprites.news(*particle_explosion(10, pos=self.rect.center, size=30, speed=5, colour=Color("#ff00ff")))

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

		for ref in self.card_map:
			if ref.card.is_destroyed():
				ref.card.rect.width -= 50

		self.card_map = [ref for ref in self.card_map if ref.card.rect.width > 1]

		self.card_map.sort(key=lambda ref: ref.card.rect.x)
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
