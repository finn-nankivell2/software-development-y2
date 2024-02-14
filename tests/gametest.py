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

from background import MatrixBackgroundRenderer
from gameutiltest import *


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
		self._current_buffer = []
		self._incorrect_buffer = []
		self._used_words = []

		with open("words") as file:
			self.wordslist = set(map(str.rstrip, file.readlines()))

	def _buffer_words(self):
		cat_current = "".join(self._current_buffer)
		history = self._incorrect_buffer.copy()
		history.append(cat_current)
		return history

	def get_view(self, expected_size=100):
		buffer = self._buffer_words()

		unpadded = list(iter(" ".join(buffer)))

		while len(unpadded) < expected_size:
			unpadded.insert(0, " ")

		return unpadded

	def is_word_valid(self, word):
		return word in self.wordslist and word not in self._used_words

	def update(self):
		keys = pygame.locals.__dict__

		for char in "abcdefghijklmnopqrstuvwxyz0123456789":
			keycode = keys["K_" + char]
			if game.input.key_pressed(keycode):
				# self._current_buffer.pop(0)
				self._current_buffer.append(char)
				break
		else:
			if game.input.key_pressed(pygame.K_SPACE):
				# self._current_buffer.append(None)
				word = "".join(self._current_buffer)

				if self.is_word_valid(word):
					print(f"VALID: {word}")
					self._used_words.append(word)
				else:
					self._incorrect_buffer.append(word)
					print(f"INVALID: {word}")

				self._current_buffer = []
		# 	elif game.input.key_pressed(pygame.K_BACKSPACE):
		# 		if game.input.key_down(pygame.K_LSHIFT):
		# 			self.buffer = [None for _ in self.buffer]
		# 		else:
		# 			self.buffer.insert(0, None)
		# 			self.buffer.pop(-1)


class FontRenderer(Sprite):
	LAYER = "FONT"

	def __init__(self):
		winsize = game.windowsystem.dimensions
		self._render_area = Vector2(120, 120)

	def update_draw(self):
		fontsize = Vector2(game.bubblefont.sheet.dimensions())
		winsize = game.windowsystem.dimensions
		rsize = self._render_area
		offset = (winsize - rsize) / 2

		expected_view_size = (rsize.x // fontsize.x) * (rsize.y // fontsize.y)

		# sliced = game.typingbuffer.buffer[-100:].copy()
		sliced = game.typingbuffer.get_view(expected_view_size)

		for y in range(0, int(rsize.y), int(fontsize.y)):
			for x in range(0, int(rsize.x), int(fontsize.x)):
				c = sliced.pop(0)
				if c == " ":
					continue

				pos = Vector2(x, y)
				game.windowsystem.screen.blit(game.bubblefont.get(c), pos + offset)


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
	game.sprites.new(MatrixBackgroundRenderer(game.windowsystem.dimensions))


game.add_module(SpritesManager, layers=["BACKGROUND", "PARTICLE", "FONT", "FOREGROUND", "UI"])
game.add_module(GameloopManager, loop_hook=do_running)
game.add_module(StateManager)
game.add_module(ClockManager)
game.add_module(
	ScalingWindowSystem,
	size=Vector2(130, 130),
	user_size=Vector2(750, 750),
	caption="typing test",
	flags=pygame.NOFRAME,
	fill_color=Color("#000000")
)
game.add_module(InputManagerScalingMouse)
game.add_module(DebugOverlayManager, fontcolour=(255, 255, 255))
game.add_module(BubbleFontModule, font_path="sprites/hacker-font.png")
game.add_module(UserTypingBuffer)

game.loop.run(mainloop)
