#!/usr/bin/python3
import pygame
from pygame import Surface, Vector2, Rect, FRect

pygame.init()

import os
import random
import math

from context import gamesystem
from gamesystem import game, GameModule
from gamesystem.mods.input import InputManagerScalingMouse
from gamesystem.mods.window import ScalingWindowSystem, MultiLayerScreenSystem
from gamesystem.mods.defaults import SpritesManager, StateManager, GameloopManager
from gamesystem.mods.debug import DebugOverlayManager

from gamesystem.common.composites import Dimensions
from gamesystem.common.sprite import Sprite
from gamesystem.common.assets import SpriteSheet


class Bullet(Sprite):
	# __slots__ = ["pos", "size", "vel", "_destroyed"]

	LAYER = "BULLET"

	def __init__(self, pos, size, angle, speed):
		self.pos = pos
		self.size = size
		self.vel = Vector2(math.cos(angle) * speed, math.sin(angle) * speed)

	def update_move(self):
		self.pos += self.vel * game.state.deltatime

		if self.pos.x < -self.size or self.pos.x > game.windowsystem.dimensions.w() + self.size:
			self.destroy()
		if self.pos.y < -self.size or self.pos.y > game.windowsystem.dimensions.h() + self.size:
			self.destroy()

	def update_draw(self):
		pygame.draw.circle(game.windowsystem.screen, (195, 95, 95), self.pos, self.size)
		pygame.draw.circle(game.windowsystem.screen, (225, 15, 95), self.pos, self.size, 1)


class Emitter(Sprite):
	LAYER = "BACKGROUND"

	def __init__(self, pos, tick):
		self.pos = pos
		self._tick = tick

	def update_move(self):
		if game.state.frames_since_start % self._tick == 0:
			a = ((game.state.frames_since_start / 5) % 6.3) + game.state.frames_since_start / 10000
			game.sprites.new(Bullet(self.pos.copy(), 3, a, 50))


class Player(Sprite):
	LAYER = "PLAYER"
	SPEED = 30
	FULLSPEED = 80

	def __init__(self, pos, size):
		self.pos = pos
		self.size = size
		self.logical_size = 2
		self._hit = False

	def update_move(self):
		self._hit = False

		vel = Vector2(0, 0)
		if game.input.key_down(pygame.K_LEFT):
			vel.x = -1
		if game.input.key_down(pygame.K_RIGHT):
			vel.x = 1
		if game.input.key_down(pygame.K_UP):
			vel.y = -1
		if game.input.key_down(pygame.K_DOWN):
			vel.y = 1

		a = math.atan2(vel.y, vel.x)
		move = Vector2(math.cos(a), math.sin(a)) if vel.length() != 0 else Vector2(0, 0)

		speed = self.SPEED if game.input.key_down(pygame.K_LSHIFT) else self.FULLSPEED

		self.pos += move * game.state.deltatime * speed
		self._do_collision()

	def _do_collision(self):
		for collide in (b.pos.distance_to(self.pos) < self.logical_size + b.size for b in game.sprites.get("BULLET")):
			if collide:
				self._hit = True
				break

	def update_draw(self):
		pygame.draw.circle(game.windowsystem.screen, (0, 0, 255) if not self._hit else (0, 0, 105), self.pos, self.size)


def do_running(self):
	self.game.state.update()
	self.game.input.update()
	self.game.sprites.update()
	game.debug.output(1 / game.state.deltatime)
	self.game.debug.update()
	self.game.windowsystem.update()


def mainloop():
	for _ in range(1):
		game.sprites.new(Emitter(game.windowsystem.dimensions.rand(), 1))
	game.sprites.new(Player(game.windowsystem.dimensions / 2, 3))


game.add_module(SpritesManager, layers=["BACKGROUND", "BULLET", "PLAYER", "FOREGROUND", "UI"])
game.add_module(GameloopManager, loop_hook=do_running)
game.add_module(StateManager)
game.add_module(
	ScalingWindowSystem,
	size=Dimensions(320, 180),
	user_size=Dimensions(1280, 720),
	caption="Bullet Stress Test",
	flags=pygame.NOFRAME
)
# game.add_module(MultiLayerScreenSystem, size=Dimensions(320, 180), num_layers=1, layer_names=["ui"])
game.add_module(InputManagerScalingMouse)
game.add_module(DebugOverlayManager, fontcolour=(255, 255, 255))

game.loop.run(mainloop)
