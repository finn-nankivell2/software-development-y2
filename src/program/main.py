#!/usr/bin/env python3
import pygame
import pygame.locals
from pygame import Surface, Vector2, Rect, FRect, Color

import os
import time
from pprint import pprint, pformat
import logging

logging.basicConfig(filename="logs/game.log", level=logging.DEBUG)

pygame.init()

import sys
import random
import math
import json
import itertools
import functools
from types import SimpleNamespace

from typing import Dict, List, Optional

from context import gamesystem
from gamesystem import game, GameModule
from gamesystem.mods.input import InputManagerScalingMouse
from gamesystem.mods.window import ScalingWindowSystem, MultiLayerScreenSystem, WInfoModule
from gamesystem.mods.defaults import SpritesManager, StateManager, GameloopManager, ClockManager
from gamesystem.mods.debug import DebugOverlayManager
from gamesystem.mods.assets import AssetManager
from gamesystem.mods.audio import AudioManagerNumChannels

from gamesystem.common.sprite import Sprite, SpriteGroup
from gamesystem.common.assets import SpriteSheet

from particles import BubbleParticleEmitter
from cards import Card, Hand, DataCard
from playspaces import Playspace

from gameutil import ScalingImageSprite, HookSprite, ScanlineImageSprite
from consts import VZERO

from gmods import TextureClippingCacheModule, BlueprintsStorageModule, PlayerStateTrackingModule
import fonts
import palette

from tooltip import Tooltip
from ui import AbstractButton, NamedButton
from turntaking import PlayerTurnTakingModue


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
	# game.sprites.new(ScanlineImageSprite(VZERO, game.assets.xpbackground), layer_override="BACKGROUND")
	# game.sprites.new(ScalingImageSprite(VZERO, game.assets.citiedlow1), layer_override="BACKGROUND")
	game.sprites.new(ScanlineImageSprite(VZERO, game.assets.citiedlow1), layer_override="BACKGROUND")

	for _, blueprint in itertools.islice(reversed(game.blueprints.icards()), 3):
		game.sprites.new(Card.from_blueprint(blueprint).with_tooltip())

	logging.debug("\n".join(k for k, _ in game.blueprints.ibuildings()))

	for _, blueprint in itertools.islice(game.blueprints.ibuildings(), 3):
		game.sprites.new(Playspace.from_blueprint(blueprint).with_tooltip())

	# game.sprites.new(Playspace.from_blueprint(game.blueprints.buildings.incinerator).with_tooltip())
	# game.sprites.new(Playspace.from_blueprint(game.blueprints.buildings.plasticrec).with_tooltip())

	# game.sprites.new(Playspace.from_blueprint(game.blueprints.buildings.incinerator).with_tooltip())
	# game.sprites.new(Playspace.from_blueprint(game.blueprints.buildings.incinerator).with_tooltip())

	game.sprites.HAND = Hand(FRect(0, game.windowsystem.dimensions.y - 20, game.windowsystem.dimensions.x, 80))
	game.sprites.new(game.sprites.HAND)

	end_turn_rect = FRect(0, 0, 140, 100)
	end_turn_rect.bottomright = game.windowsystem.dimensions - Vector2(20, 20)

	def end_turn_behaviour(*_):
		game.playerturn.end_turn()

	game.sprites.new(NamedButton(end_turn_rect, "End Turn", onclick=end_turn_behaviour), layer_override="UI")

	logging.debug("---------- ASSETS ----------")
	logging.debug(pformat(game.assets.all()))
	logging.debug("---------- PLAYSPACES ----------")
	logging.debug(pformat([space.data for space in game.sprites.get("PLAYSPACE")]))
	logging.debug("---------- SPACES TEXTURE ----------")
	logging.debug(pformat([space._picture for space in game.sprites.get("PLAYSPACE")]))
	logging.debug("---------- PLAYER STATE ----------")
	logging.debug(game.playerstate)

	logging.debug("-------------------- GAME START --------------------\n\n")


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

	game.add_module(WInfoModule)

	game.add_module(
		ScalingWindowSystem,
		size=game.winfo.display_size,
		user_size=game.winfo.display_size,
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

	game.add_module(PlayerStateTrackingModule)
	game.add_module(PlayerTurnTakingModue)

	with open("data/blueprints.json") as file:
		game.add_module(BlueprintsStorageModule, blueprints=json.load(file))

	game.loop.run(mainloop)
