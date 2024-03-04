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



class Hand(Sprite):
	LAYER = "FOREGROUND"

	def __init__(self, rect):
		self.rect = rect
		self.currently_dragged = None



class Card(Sprite):
	LAYER = "CARD"

	def __init__(self, pos, size, colour):
		self.rect = FRect(pos, size)
		self.colour = colour
		self.hand_locked = False
		self.dragged = False
		self.mouse_offset = Vector2(0, 0)
		self.held_frames = 0

	def update_move(self):
		hand = game.sprites.HAND

		if game.input.mouse_pressed(0) and hand.currently_dragged is None:
			if hand.currently_dragged is not None:
				assert False

			if self.rect.collidepoint(game.input.mouse_pos()) and not self.dragged:
				self.dragged = True
				self.hand_locked = False
				self.mouse_offset = game.input.mouse_pos() - self.rect.topleft
				hand.currently_dragged = self
				print(hand.currently_dragged)

		if not game.input.mouse_down(0):
			self.dragged = False

		if not self.dragged:
			self.hand_locked = True
			self.held_frames = 0
		else:
			self.rect.topleft = game.input.mouse_pos() - self.mouse_offset
			self.held_frames += 1

		if self.hand_locked:
			travel = (hand.rect.bottom - self.rect.bottom)
			self.rect.y += max(2, travel / 10)

			if abs(travel) < 5:
				self.hand_locked = False
				self.rect.bottom = hand.rect.bottom
		else:
			if hand.currently_dragged is self:
				hand.currently_dragged = None


	def update_draw(self):
		if self.dragged:
			shadow_rect = self.rect.copy()
			shadow_rect.topleft += Vector2(self.rect.size) / max(self.held_frames, 10)
			pygame.draw.rect(game.windowsystem.screen, Color("#ffffff"), shadow_rect, border_radius=5)
		pygame.draw.rect(game.windowsystem.screen, self.colour, self.rect, border_radius=5)


def mainmenu():
	pass


def spritefollow():
	# game.sprites.new(FollowParticle(pos=game.windowsystem.dimensions / 2))
	game.sprites.new(Card((200, 100), (150, 220), Color("#000000")))
	game.sprites.new(Card((400, 100), (150, 220), Color("#000000")))
	game.sprites.new(Card((600, 100), (150, 220), Color("#000000")))

	game.sprites.HAND = Hand(FRect(0, 740, 1280, 60))
	game.sprites.new(game.sprites.HAND)


def do_running(self):
	self.game.clock.update()
	self.game.state.update()
	self.game.input.update()
	self.game.sprites.update()
	self.game.debug.update()
	self.game.windowsystem.update()


if __name__ == "__main__":
	game.add_module(SpritesManager, layers=["MANAGER", "BACKGROUND", "PARTICLE", "CARD", "FONT", "FOREGROUND", "UI"])
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
