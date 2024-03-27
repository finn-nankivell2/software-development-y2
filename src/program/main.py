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
from gamesystem.mods.audio import AudioManagerNumChannels

from gamesystem.common.sprite import Sprite, SpriteGroup
from gamesystem.common.assets import SpriteSheet

from particles import BubbleParticleEmitter
from cards import Card, Hand, DataCard
from playspaces import Playspace

from gameutil import ScalingImageSprite
from consts import VZERO

from gmods import TextureClippingCacheModule, BlueprintsStorageModule
import fonts


def mainloop():
	with open("data/colours.json") as file:
		gradient = json.load(file)

	gradient = list(map(Color, gradient))

	game.windowsystem.set_fill_color(gradient[0])
	# bg_grad = [gradient[0], gradient[1]]

	# bg_particles = BubbleParticleEmitter(pos=game.windowsystem.dimensions / 2, colours=bg_grad)
	# for _ in range(1000):
	# 	bg_particles.update_move()
	# game.sprites.new(bg_particles)
	game.sprites.new(ScalingImageSprite(VZERO, game.assets.xpbackground), layer_override="BACKGROUND")

	for blueprint in reversed(game.blueprints.values()):
		game.sprites.new(Card.from_blueprint(blueprint))

	# for _ in range(2):
	# 	game.sprites.new(Card.from_blueprint(game.blueprints.aluminium))

	# for _ in range(2):
	# 	game.sprites.new(Card.from_blueprint(game.blueprints.paper))

	# for _ in range(2):
	# 	game.sprites.new(Card.from_blueprint(game.blueprints.plastic))

	# for _ in range(1):
	# 	game.sprites.new(Card.from_blueprint(game.blueprints.compost))

	# game.sprites.new(Card((400, 100), (150, 220), Color("#ff0000")))
	# game.sprites.new(Card((600, 100), (150, 220), Color("#0000ff")))
	# game.sprites.new(Card((600, 100), (150, 220), Color("#00ff00")))
	# game.sprites.new(Card((600, 100), (150, 220), Color("#ffaa00")))

	game.sprites.new(Playspace(Rect(100, 100, 400, 250), game.assets.buildingbg))

	game.sprites.new(Playspace(Rect(800, 100, 400, 250), game.assets.buildingbg))

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
		fill_color=Color("#000000")
	)

	# #54A200

	game.add_module(InputManagerScalingMouse)
	game.add_module(DebugOverlayManager, fontcolour=(255, 255, 255))

	with open("data/assets.json") as file:
		jdict = json.load(file)
		textures, sfx = jdict["textures"], jdict["sfx"]

		game.add_module(AssetManager, assets=textures)
		game.add_module(AudioManagerNumChannels, sounds=sfx, num_channels=30)

	game.add_module(TextureClippingCacheModule)

	with open("data/blueprints.json") as file:
		game.add_module(BlueprintsStorageModule, blueprints=json.load(file))

	game.loop.run(mainloop)
