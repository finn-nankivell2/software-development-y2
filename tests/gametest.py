#!/usr/bin/python3
import pygame
import pygame.locals
from pygame import Surface, Vector2, Rect, FRect, Color

pygame.init()

import os
import random
import math
from types import SimpleNamespace

from context import gamesystem
from gamesystem import game, GameModule
from gamesystem.mods.input import InputManagerScalingMouse
from gamesystem.mods.window import ScalingWindowSystem, MultiLayerScreenSystem
from gamesystem.mods.defaults import SpritesManager, StateManager, GameloopManager, ClockManager
from gamesystem.mods.debug import DebugOverlayManager

from gamesystem.common.sprite import Sprite
from gamesystem.common.assets import SpriteSheet


class BubbleFontModule(GameModule):
	IDMARKER = "bubblefont"

	def create(self, font_path="sprites/fontblock-unblocked.png"):
		self.raw = pygame.image.load(font_path)

		ALPHA = "abcdefghijklmnopqrstuvwxyz0123456789"
		self.CHARACTERS = [c for c in ALPHA]

		self.sheet = SpriteSheet(self.raw, (12, 12), names=self.CHARACTERS)

	def get(self, k):
		return self.sheet.__dict__[k]


class UserTypingBuffer(GameModule):
	IDMARKER = "typingbuffer"

	REQUIREMENTS = ["input"]

	def create(self):
		# self.buffer = [None for _ in range(101-26)] + list(iter("abcdefghijklmnopqrstuvwxyz"))
		self.buffer = [None for _ in range(101)]

	def update(self):
		keys = pygame.locals.__dict__

		for char in "abcdefghijklmnopqrstuvwxyz0123456789":
			keycode = keys["K_" + char]
			if game.input.key_pressed(keycode):
				self.buffer.pop(0)
				self.buffer.append(char)
				break
		else:
			if game.input.key_pressed(pygame.K_SPACE):
				self.buffer.pop(0)
				self.buffer.append(None)

			elif game.input.key_pressed(pygame.K_BACKSPACE):
				if game.input.key_down(pygame.K_LSHIFT):
					self.buffer = [None for _ in self.buffer]
				else:
					self.buffer.insert(0, None)
					self.buffer.pop(-1)


class FontRenderer(Sprite):
	LAYER = "FOREGROUND"

	def __init__(self):
		pass

	def update_draw(self):
		fontsize = Vector2(game.bubblefont.sheet.dimensions())
		winsize = game.windowsystem.dimensions

		sliced = game.typingbuffer.buffer[-100:].copy()

		for y in range(0, int(winsize.y), int(fontsize.y)):
			for x in range(0, int(winsize.x), int(fontsize.x)):
				c = sliced.pop(0)
				if c is None:
					continue

				game.windowsystem.screen.blit(game.bubblefont.get(c), (x, y))


class BackgroundRenderer(Sprite):
	LAYER = "BACKGROUND"

	def __init__(self, size, num=10, colours=None):
		self._surfaces = [Surface(size) for _ in range(num)]

		self._colours = colours
		if self._colours is None:
			self._colours = {4: Color("#37ae2f"), 90: Color("#000000"), 4: Color("#076e0f"), 2: Color("#00ff00")}

		for surf in self._surfaces:
			w, h = surf.get_size()
			surf.lock()
			for x in range(w):
				for y in range(h):
					surf.set_at((x, y), self.get_random_colour())

			surf.unlock()

	def get_random_colour(self):
		seed = random.randint(0, 100)
		prev = 0

		for k, v in self._colours.items():
			if k + prev >= seed:
				return v
			prev += k

		return Color("#000000")

	def update_draw(self):
		game.windowsystem.screen.blit(random.choice(self._surfaces), (0, 0))


def do_running(self):
	self.game.clock.update()
	self.game.state.update()
	self.game.input.update()
	self.game.typingbuffer.update()
	self.game.sprites.update()
	self.game.debug.update()
	self.game.windowsystem.update()


def mainloop():
	game.sprites.new(FontRenderer())
	game.sprites.new(BackgroundRenderer(game.windowsystem.dimensions, num=50))


game.add_module(SpritesManager, layers=["BACKGROUND", "BULLET", "PLAYER", "FOREGROUND", "UI"])
game.add_module(GameloopManager, loop_hook=do_running)
game.add_module(StateManager)
game.add_module(ClockManager)
game.add_module(
	ScalingWindowSystem,
	size=Vector2(120, 120),
	user_size=Vector2(720, 720),
	caption="typing test",
	flags=pygame.NOFRAME,
	fill_color=Color("#000000")
)
game.add_module(InputManagerScalingMouse)
game.add_module(DebugOverlayManager, fontcolour=(255, 255, 255))
game.add_module(BubbleFontModule, font_path="sprites/hacker-font.png")
game.add_module(UserTypingBuffer)

game.loop.run(mainloop)
