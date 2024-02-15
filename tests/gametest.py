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

from background import MatrixBackgroundRenderer, RandomizedBackgroundRenderer
from gameutiltest import *

from enum import IntEnum


class BubbleFontModule(GameModule):
	IDMARKER = "bubblefont"

	def create(self, font_path="sprites/fontblock-unblocked.png"):
		self.raw = pygame.image.load(font_path).convert_alpha()

		ALPHA = "abcdefghijklmnopqrstuvwxyz0123456789"
		self.CHARACTERS = [c for c in ALPHA] + ["STOP"]

		self.sheet = SpriteSheet(self.raw, (12, 12), names=self.CHARACTERS)

	def get(self, k):
		return self.sheet.get_by_name(k)

	def render(self, characters):
		dims = self.sheet.dimensions()
		size = Vector2(dims[0] * len(characters), dims[1])
		surface = Surface(size, pygame.SRCALPHA)

		for x, c in zip(range(0, self.raw.get_width(), dims[1]), characters):
			if c == " ":
				continue

			surface.blit(self.get(c), (x, 0))

		return surface


class UserTypingBuffer(GameModule):
	IDMARKER = "typingbuffer"

	REQUIREMENTS = ["input"]

	def create(self):
		self.reset_buffers()

		with open("words") as file:
			self.wordslist = set(map(str.rstrip, file.readlines()))

	def reset_buffers(self):
		self._current_buffer = []
		self._incorrect_buffer = []
		self._used_words = []

	def _buffer_words(self):
		return history

	def get_view(self, expected_size=100):
		cat_current = "".join(self._current_buffer)
		joinchar = " "

		buffer_incorrect = self._incorrect_buffer.copy()
		buffer_incorrect = joinchar.join(buffer_incorrect)
		buffer_incorrect = joinchar + buffer_incorrect if buffer_incorrect else buffer_incorrect

		unpadded = list(iter(buffer_incorrect + joinchar + cat_current))

		if len(unpadded) > expected_size:
			game.loop.run(failstate)
			self.reset_buffers()

		while len(unpadded) < expected_size:
			unpadded.insert(0, " ")

		return unpadded

	def _spawn_popped_particle(self, word):
		fontdims = Vector2(game.bubblefont.sheet.dimensions())

		botright = Vector2(120, 120)
		botright.y -= fontdims.y
		botright.x -= (len(word) - 0.5) * int(fontdims.x)

		game.sprites.new(PoppedFontParticle(botright, word))

	def is_word_valid(self, word):
		return len(word) > 1 and word not in self._used_words and word in self.wordslist

	def update(self):
		keys = pygame.locals.__dict__

		for char in "abcdefghijklmnopqrstuvwxyz0123456789":
			keycode = keys["K_" + char]
			if game.input.key_pressed(keycode):
				self._current_buffer.append(char)
				break
		else:
			if game.input.key_pressed(pygame.K_SPACE):
				word = "".join(self._current_buffer)

				if self.is_word_valid(word):
					print(f"VALID: {word}")
					self._used_words.append(word)
					self._spawn_popped_particle(word)
				else:
					self._incorrect_buffer.append(word)
					print(f"INVALID: {word}")

				self._current_buffer = []


class PoppedFontParticle(Sprite):
	LAYER = "PARTICLE"
	VEL = Vector2(0, -0.5)

	def __init__(self, pos, characters):
		self.pos = pos
		self._ticker = 255

		self._surface = game.bubblefont.render(characters)

	def update_move(self):
		self.pos += PoppedFontParticle.VEL
		self._ticker -= 8

		if self._ticker < 1:
			self.destroy()

	def update_draw(self):
		self._surface.set_alpha(self._ticker)
		game.windowsystem.screen.blit(self._surface, self.pos)


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

				if c == "_":
					use_asset = game.bubblefont.get("STOP")

				else:
					use_asset = game.bubblefont.get(c)

				pos = Vector2(x, y)
				game.windowsystem.screen.blit(use_asset, pos + offset)


class GameOverMessage(Sprite):
	LAYER = "UI"

	def __init__(self):
		self.message = "game over"
		self._surface = game.bubblefont.render(self.message)

	def update_move(self):
		if game.input.key_pressed(pygame.K_r):
			game.loop.run(mainloop)

	def update_draw(self):
		pos = (game.windowsystem.dimensions - self._surface.get_size()) / 2
		game.windowsystem.screen.blit(self._surface, pos)


def do_running(self):
	self.game.clock.update()
	self.game.state.update()
	self.game.input.update()
	self.game.typingbuffer.update()
	self.game.sprites.update()
	self.game.debug.update()
	self.game.windowsystem.update()


def failstate():
	game.sprites.purge_preserve("BACKGROUND")
	game.sprites.new(GameOverMessage())


def mainloop():
	game.sprites.purge()
	game.typingbuffer.reset_buffers()
	game.sprites.new(FontRenderer())
	game.sprites.new(MatrixBackgroundRenderer(game.windowsystem.dimensions))


if __name__ == "__main__":
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
