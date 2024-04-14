#!/usr/bin/env python3
import pygame
import pygame.locals
from pygame import Surface, Vector2, Rect, FRect, Color

import os
import time
from pprint import pprint, pformat
import logging

if os.path.exists("logs") and os.path.isdir("logs"):
	logging.basicConfig(filename="logs/game.log", level=logging.DEBUG)
else:
	logging.basicConfig(level=logging.ERROR)

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
from gamesystem.mods.window import ScalingWindowSystem, MultiLayerScreenSystem, WInfoModule, AspectScalingWindowSystem
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

from gmods import TextureClippingCacheModule, BlueprintsStorageModule, PlayerStateTrackingModule, CardSpawningModule
import fonts
import palette

from tooltip import Tooltip
from ui import AbstractButton, NamedButton, ProgressBar, TargettingProgressBar, DodgingProgressBar
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
	game.sprites.new(ScalingImageSprite(VZERO, game.assets.citiedlow1), layer_override="BACKGROUND")
	# game.sprites.new(ScanlineImageSprite(VZERO, game.assets.citiedlow1), layer_override="BACKGROUND")

	# for _, blueprint in itertools.islice(reversed(game.blueprints.icards()), 3):
	# 	game.sprites.new(Card.from_blueprint(blueprint).with_tooltip())

	# game.sprites.new(Card.from_blueprint(game.blueprints.cards.mixed).with_tooltip())

	# logging.debug("\n".join(k for k, _ in game.blueprints.ibuildings()))

	# for _, blueprint in itertools.islice(reversed(game.blueprints.ibuildings()), 3):
	# 	game.sprites.new(Playspace.from_blueprint(blueprint).with_tooltip())

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

	pbar_rect = FRect(0, 0, 400, 43)
	pbar_rect.topright = (game.windowsystem.dimensions.x, 100)
	game.spriteglobals.pollution_bar = DodgingProgressBar(pbar_rect, "Pollution", target="pollution").with_tooltip("Pollution increases when cards are left unplayed. If it reaches 100%, you are dead")
	game.sprites.new(game.spriteglobals.pollution_bar, layer_override="FOREGROUND")

	pbar_rect = FRect(0, 0, 200, 43)
	pbar_rect.topright = (game.windowsystem.dimensions.x, 170)
	game.sprites.new(DodgingProgressBar(pbar_rect, "Funds", target="funds"), layer_override="FOREGROUND")

	game.playerturn.scene_start()
	game.playerturn.next_turn()

	logging.debug("---------- ASSETS ----------")
	logging.debug(pformat(game.assets.all()))
	logging.debug("---------- PLAYSPACES ----------")
	logging.debug(pformat([space.data for space in game.sprites.get("PLAYSPACE")]))
	logging.debug("---------- SPACES TEXTURE ----------")
	logging.debug(pformat([space._picture for space in game.sprites.get("PLAYSPACE")]))
	logging.debug("---------- PLAYER STATE ----------")
	logging.debug(game.playerstate)

	logging.debug("-------------------- GAME START --------------------\n\n")

	game.sprites.new(HookSprite(debug_hook), layer_override="MANAGER")


def debug_hook():
	pass
	# game.debug.output(f"cards: {len(game.sprites.get('CARD'))}")
	# game.debug.output(len(game.sprites.HAND.card_map))
	# game.debug.output([card.data.title for card in game.sprites.get("CARD")])
	# logging.debug([card.data.title for card in game.sprites.get("CARD")])
	# logging.debug(game.sprites.get("CARD"))


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

	game.add_module(InputManagerScalingMouse)
	game.add_module(DebugOverlayManager, fontcolour=Color("#ff00ff"))


	with open("data/assets.json") as file:
		jdict = json.load(file)
		textures, sfx = jdict["textures"], jdict["sfx"]

		game.add_module(AssetManager, assets=textures)
		game.add_module(AudioManagerNumChannels, sounds=sfx, num_channels=30)

	with open("data/blueprints.json") as file:
		game.add_module(BlueprintsStorageModule, blueprints=json.load(file))

	game.add_module(CardSpawningModule)
	game.add_module(TextureClippingCacheModule)
	game.add_module(PlayerStateTrackingModule)

	game.add_module(PlayerTurnTakingModue)
	game.loop.run(mainloop)
