#!/usr/bin/env python3
import pygame
import pygame.locals
from pygame import Surface, Vector2, Rect, FRect, Color
import os

pygame.init()

import sys
import random
import math
import json
from types import SimpleNamespace

from typing import Dict, List, Optional

from context import *
from gamesystem import game, GameModule
from gamesystem.mods.input import InputManagerScalingMouse
from gamesystem.mods.window import ScalingWindowSystem, MultiLayerScreenSystem
from gamesystem.mods.defaults import SpritesManager, StateManager, GameloopManager, ClockManager
from gamesystem.mods.debug import DebugOverlayManager

from gamesystem.common.sprite import Sprite, SpriteGroup
from gamesystem.common.assets import SpriteSheet

from gameutil import *
from dataclasses import dataclass


class DebugRect():

	def update_draw(self):
		pygame.draw.rect(game.windowsystem.screen, Color("#ff00ff"), self.rect)


class Playspace(DebugRect, Sprite):
	LAYER = "PLAYSPACE"

	def __init__(self, rect, colour):
		self.rect = rect
		self.colour = colour

	def update_move(self):
		pass

	def update_draw(self):
		pygame.draw.rect(game.windowsystem.screen, self.colour, self.rect, border_radius=5)


class Card(Sprite):
	LAYER = "CARD"
	PICKME_SHIFT_AMT = 50

	def __init__(self, pos, size, colour):
		self.rect = FRect(pos, size)
		self.colour = colour
		self.hand_locked = False  # If card is drifting towards or in hand
		self.dragged = False  # If card is currently held by the mouse
		self.mouse_offset = Vector2(0, 0)  # Point where the mouse grabbed the card
		self.held_frames = 0  # How many frames card has been held for

	def playspace_collide(self):
		for playspace in game.sprites.get("PLAYSPACE"):
			if playspace.rect.colliderect(self.rect):
				return playspace

		return None

	def is_playable(self):
		return self.playspace_collide() is not None

	def mouse_over_me(self):
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
		else:
			self.hand_locked = True
			self.held_frames = 0

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

	def destroy(self):
		super().destroy()
		game.sprites.news(*particle_explosion(10, pos=self.rect.center, size=30, speed=5, colour=self.colour))

	def update_draw(self):
		if self.dragged:
			shadow_rect = self.rect.copy()
			shadow_rect.topleft += Vector2(self.rect.size) / max(self.held_frames, 10)
			pygame.draw.rect(game.windowsystem.screen, Color("#ffffff"), shadow_rect, border_radius=5)

		pygame.draw.rect(game.windowsystem.screen, self.colour, self.rect, border_radius=5)


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


def mainmenu():
	pass


def spritefollow():
	gradient = [
		"#a52adb",
		"#982ad9",
		"#8b2ad7",
		"#7e2ad5",
		"#712ad3",
		"#642ad1",
		"#572acf",
		"#4a2acd",
		"#3d2acb",
		"#302ac9"
	]

	gradient = list(map(Color, gradient))

	game.windowsystem.set_fill_color(gradient[0])
	bg_grad = gradient[:2]

	bg_particles = FollowParticle(pos=game.windowsystem.dimensions / 2, colours=bg_grad)
	for _ in range(1000):
		bg_particles.update_move()

	game.sprites.new(bg_particles)

	for c in gradient[-5:]:
		game.sprites.new(Card((200, 100), (150, 220), c))

	# game.sprites.new(Card((400, 100), (150, 220), Color("#ff0000")))
	# game.sprites.new(Card((600, 100), (150, 220), Color("#0000ff")))
	# game.sprites.new(Card((600, 100), (150, 220), Color("#00ff00")))
	# game.sprites.new(Card((600, 100), (150, 220), Color("#ffaa00")))

	game.sprites.new(Playspace(Rect(100, 100, 400, 250), Color("#ffffff")))

	game.sprites.HAND = Hand(FRect(0, 780, 1280, 80))
	game.sprites.new(game.sprites.HAND)


def do_running(self):
	self.game.clock.update()
	self.game.state.update()
	self.game.input.update()
	self.game.sprites.update()
	self.game.debug.update()
	self.game.windowsystem.update()


if __name__ == "__main__":
	game.add_module(
		SpritesManager, layers=["MANAGER", "BACKGROUND", "PLAYSPACE", "CARD", "PARTICLE", "FONT", "FOREGROUND", "UI"]
	)
	game.add_module(GameloopManager, loop_hook=do_running)
	game.add_module(StateManager)
	game.add_module(ClockManager)

	game.add_module(
		ScalingWindowSystem,
		size=Vector2(1280, 800),
		user_size=Vector2(1280, 800),
		caption="program",
		flags=pygame.NOFRAME,
		fill_color=Color("#6e1698")
	)
	game.add_module(InputManagerScalingMouse)
	game.add_module(DebugOverlayManager, fontcolour=(255, 255, 255))

	game.loop.run(spritefollow)
