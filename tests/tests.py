#!/usr/bin/python3

# Integration Tests
import pytest

import pygame

from context import gamesystem
from gamesystem import GameNamespace, mods
from gamesystem.common import composites

import gamesystem.mods.defaults
from gamesystem.mods.window import BasicWindowSystem, ScalingWindowSystem, MultiLayerScreenSystem
from gamesystem.mods.input import InputManager, InputManagerScalingMouse
from gamesystem.mods.input import InputManager, InputManagerScalingMouse


class BaseTestSprite():
	_destroyed = False
	LAYER = "FG"

	def __init__(self):
		pass

	def update_move(self):
		pass

	def update_draw(self):
		pass


def test_sprites_destroy():
	game = GameNamespace()

	class InstantDestroySprite(BaseTestSprite):

		def update_move(self):
			self._destroyed = True

	game.add_modules(*mods.defaults.default_modules())
	game.sprites.news(*[InstantDestroySprite() for _ in range(100)])

	assert len(game.sprites) == 100
	game.loop.do_running()
	assert len(game.sprites) == 0


def test_game_state():
	game = GameNamespace()

	game.add_module(mods.defaults.StateManager)
	game.add_modules(*mods.defaults.default_modules())
	game.loop.set_hook(lambda self: self.game.state.update())

	assert game.state.frames_since_start == 0
	game.loop.do_running()
	assert game.state.frames_since_start == 1
	game.loop.do_running()
	assert game.state.frames_since_start == 2


def test_sprite_movement():
	game = GameNamespace()

	class MovingSprite(BaseTestSprite):
		x = 0

		def update_move(self):
			self.x += 20

	game.add_modules(*mods.defaults.default_modules())

	sprite_ref = MovingSprite()
	game.sprites.new(sprite_ref)

	assert sprite_ref.x == 0
	game.loop.do_running()
	assert sprite_ref.x == 20


def test_create_basic_window():
	game = GameNamespace()
	game.add_modules(*mods.defaults.default_modules())
	game.add_module(BasicWindowSystem, size=(800, 600))


def test_run_basic_window_testerinput():
	import math

	game = GameNamespace()

	class PlayerController(BaseTestSprite):
		pos = pygame.Vector2(10, 10)
		c = pygame.Color(186, 75, 105)
		toggle = True

		def update_move(self):
			keys = pygame.key.get_pressed()

			move = pygame.Vector2(0, 0)
			if game.input.key_down(pygame.K_a):
				move.x -= 1
			if game.input.key_down(pygame.K_d):
				move.x += 1
			if game.input.key_down(pygame.K_w):
				move.y -= 1
			if game.input.key_down(pygame.K_s):
				move.y += 1

			a = math.atan2(move.y, move.x)
			move = pygame.Vector2(math.cos(a), math.sin(a)) if abs(move.x) + abs(move.y) != 0 else pygame.Vector2(0, 0)

			self.pos += move * 380 * game.state.deltatime

			if game.input.key_pressed(pygame.K_SPACE) or game.input.mouse_pressed(0):
				self.toggle = not self.toggle

			if self.pos.x < 0:
				self.pos.x = 0
			if self.pos.x > game.windowsystem.dimensions.x:
				self.pos.x = game.windowsystem.dimensions.x

			if self.pos.y < 0:
				self.pos.y = 0
			if self.pos.y > game.windowsystem.dimensions.y:
				self.pos.y = game.windowsystem.dimensions.y

		def update_draw(self):
			mag = self.pos.magnitude() / game.windowsystem.dimensions.magnitude()
			boost = pygame.Color(30, 30, 30)

			fgc = pygame.Color(int(mag * 200), int(mag * 127), 35 + int(mag * 65), 255) + boost
			bgc = pygame.Color(int(mag * 127), int(mag * 23), int(mag * 200), 255) + boost

			pygame.draw.circle(game.screens.layers.foreground, fgc, self.pos, 25 if self.toggle else 10)
			pygame.draw.circle(game.screens.layers.background, bgc, self.pos * 1.2, 25 if self.toggle else 10)

			pygame.draw.circle(
				game.screens.layers.background, bgc, game.input.mouse_pos() + (game.input.mouse_movement() * -1), 8
			)
			pygame.draw.circle(game.screens.layers.background, fgc, game.input.mouse_pos(), 8)

	def _sethook(self):
		self.game.input.update()
		self.game.sprites.update()
		self.game.screens.update()
		self.game.windowsystem.update()
		self.game.state.update()

	game.add_module(mods.defaults.StateManager)
	game.add_modules(*mods.defaults.default_modules())

	game.add_module(ScalingWindowSystem, size=(640, 360), user_size=(1280, 720), flags=pygame.SCALED)
	game.add_module(MultiLayerScreenSystem, size=(640, 360), num_layers=2, layer_names=["background", "foreground"])

	game.add_module(InputManagerScalingMouse)

	game.loop.set_hook(_sethook)
	game.sprites.new(PlayerController())

	with pytest.raises(SystemExit):
		game.loop.run(lambda: None)
