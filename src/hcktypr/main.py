#!/usr/bin/env python3
import pygame
import pygame.locals
from pygame import Surface, Vector2, Rect, FRect, Color

pygame.init()

import os
import sys
import random
import math
from types import SimpleNamespace

from context import *
from gamesystem import game, GameModule
from gamesystem.mods.input import InputManagerScalingMouse
from gamesystem.mods.window import ScalingWindowSystem, MultiLayerScreenSystem
from gamesystem.mods.defaults import SpritesManager, StateManager, GameloopManager, ClockManager
from gamesystem.mods.debug import DebugOverlayManager

from gamesystem.common.sprite import Sprite
from gamesystem.common.assets import SpriteSheet

from background import MatrixBackgroundRenderer, RandomizedBackgroundRenderer
from gameutil import *

from enum import IntEnum
from dataclasses import dataclass


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

	TIMER_LENGTH_MAX = 5.0
	TIMER_LENGTH_MIN = 2.0
	TIMER_LENGTH = 5.0

	def create(self):
		self.reset_buffers()

		with open("words") as file:
			self.wordslist = set(map(str.rstrip, file.readlines()))

	def reset_buffers(self):
		self._current_buffer = []
		self._incorrect_buffer = []
		self._used_words = []

		self.word_timer = game.state.timer(UserTypingBuffer.TIMER_LENGTH)
		self._frozen = False
		self.TIMER_LENGTH = UserTypingBuffer.TIMER_LENGTH_MAX

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
			self._frozen = True

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
		if self._frozen:
			return

		keys = pygame.locals.__dict__

		if self.word_timer.complete():
			game.loop.run(failstate)
			self._frozen = True

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
					game.sprites.score.score += len(word)
				else:
					self._incorrect_buffer.append(word)
					print(f"INVALID: {word}")

				self.word_timer = game.state.timer(UserTypingBuffer.TIMER_LENGTH)
				self._current_buffer = []

				if self.TIMER_LENGTH > UserTypingBuffer.TIMER_LENGTH_MIN:
					self.TIMER_LENGTH -= 0.1


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

		self._tickdown_size = Vector2(winsize.x, 10)
		self._tickdown = MatrixBackgroundRenderer(self._tickdown_size, crange=(Color("#000000"), Color("#00ff00")))

	def update_move(self):
		self._tickdown.update_move()

	def update_draw(self):
		fontsize = Vector2(game.bubblefont.sheet.dimensions())
		winsize = game.windowsystem.dimensions
		rsize = self._render_area
		offset = (winsize - rsize)
		offset.x = offset.x / 2

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

		self._tickdown.update_draw()

		tickstart = int(winsize.x * (1.0 - game.typingbuffer.word_timer.ratio()))
		tickcover = winsize.x - tickstart
		pygame.draw.rect(game.windowsystem.screen, Color("#000000"), (tickstart, 0, tickcover, self._tickdown_size.y))


class GameOverMessage(Sprite):
	LAYER = "UI"

	def __init__(self, score=0):
		self._surface = game.bubblefont.render("game over")
		self._score_surface = game.bubblefont.render(f"score {score}")

	def update_move(self):
		if game.input.key_pressed(pygame.K_r):
			game.loop.run(mainloop)

	def update_draw(self):
		pos = Vector2(game.windowsystem.dimensions - self._surface.get_size()) / 2
		pos -= Vector2(0, 24)
		game.windowsystem.screen.blit(self._surface, pos)

		pos_score = Vector2(game.windowsystem.dimensions - self._score_surface.get_size()) / 2
		# pos_score += Vector2(0, 24)
		game.windowsystem.screen.blit(self._score_surface, pos_score)


class UiMat(Sprite):
	LAYER = "UI"

	@dataclass
	class Button:
		surf: Surface
		text: str
		callback: any

	def __init__(self, buttons, offset=Vector2(0, 0), start_idx=0):
		self._buttons = ((game.bubblefont.render(btext), btext, callback) for btext, callback in buttons)
		self._buttons = [UiMat.Button(*items) for items in self._buttons]
		self._idx = start_idx
		self.offset = offset

	def _idx_inbounds(self):
		if self._idx < 0:
			self._idx = 0
		if self._idx >= len(self._buttons):
			self._idx = len(self._buttons)-1

	def bcurrent(self):
		return self._buttons[self._idx]

	def update_move(self):
		if game.input.key_pressed(pygame.K_UP):
			self._idx -= 1
			self._idx_inbounds()
			if self.bcurrent().callback is None:
				self._idx += 1

		if game.input.key_pressed(pygame.K_DOWN):
			self._idx += 1
			self._idx_inbounds()

			if self.bcurrent().callback is None:
				self._idx -= 1

		if game.input.key_pressed(pygame.K_SPACE):
			self.bcurrent().callback()

	def update_draw(self):
		for i, button in enumerate(self._buttons):

			pos = Vector2(game.windowsystem.dimensions.x / 2,
							(i + 1) * 20) - Vector2(button.surf.get_size()) / 2 + self.offset
			game.windowsystem.screen.blit(button.surf, pos)

			if i == self._idx:
				stop = game.bubblefont.get("STOP")
				game.windowsystem.screen.blit(stop, pos - Vector2(12, 0))


class ScoreLogger(Sprite):

	def __init__(self):
		self.score = 0


def do_running(self):
	self.game.clock.update()
	self.game.state.update()
	self.game.input.update()
	self.game.typingbuffer.update()
	self.game.sprites.update()
	self.game.debug.update()
	self.game.windowsystem.update()


def failstate():
	score = game.sprites.score.score
	game.sprites.purge_preserve("BACKGROUND")
	game.sprites.new(GameOverMessage(score))


def mainloop():
	game.sprites.purge_preserve("BACKGROUND")
	game.sprites.new(FontRenderer())
	game.typingbuffer.reset_buffers()
	game.sprites.score = ScoreLogger()


def mainmenu():
	game.sprites.new(
		UiMat([
			["hcktypr", None],
			["play", lambda: game.loop.run(mainloop)],
			["exit", lambda: sys.exit()],
		],
				offset=Vector2(0, 20),
				start_idx=1)
	)
	game.typingbuffer._frozen = True


if __name__ == "__main__":
	game.add_module(SpritesManager, layers=["BACKGROUND", "PARTICLE", "FONT", "FOREGROUND", "UI"])
	game.add_module(GameloopManager, loop_hook=do_running)
	game.add_module(StateManager)
	game.add_module(ClockManager)
	game.add_module(
		ScalingWindowSystem,
		size=Vector2(130, 130),  # Cant be smaller than 120 120
		user_size=Vector2(750, 750),
		caption="typing test",
		flags=pygame.NOFRAME,
		fill_color=Color("#000000")
	)
	game.add_module(InputManagerScalingMouse)
	game.add_module(DebugOverlayManager, fontcolour=(255, 255, 255))
	game.add_module(BubbleFontModule, font_path="sprites/hacker-font.png")
	game.add_module(UserTypingBuffer)

	game.sprites.new(RandomizedBackgroundRenderer(game.windowsystem.dimensions, num=20))

	game.loop.run(mainmenu)
