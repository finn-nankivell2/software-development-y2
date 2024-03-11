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

from context import gamesystem
from gamesystem import game, GameModule
from gamesystem.mods.input import InputManagerScalingMouse
from gamesystem.mods.window import ScalingWindowSystem, MultiLayerScreenSystem
from gamesystem.mods.defaults import SpritesManager, StateManager, GameloopManager, ClockManager
from gamesystem.mods.debug import DebugOverlayManager
from gamesystem.mods.assets import AssetManager

from gamesystem.common.sprite import Sprite, SpriteGroup
from gamesystem.common.assets import SpriteSheet

from gameutil import FollowParticle
from cards import Card, Hand, Playspace

from gmods import TextureClippingCacheModule


def mainmenu():
	pass


def spritefollow():
	with open("colours.json") as file:
		gradient = json.load(file)

	gradient = list(map(Color, gradient))

	game.windowsystem.set_fill_color(gradient[0])
	bg_grad = [gradient[0], gradient[1]]

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

	game.sprites.new(Playspace(Rect(100, 100, 400, 250), gradient[len(gradient) // 2]))

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
	game.add_module(AssetManager, rock="assets/rock2.jpg")
	game.add_module(TextureClippingCacheModule)

	game.loop.run(spritefollow)
