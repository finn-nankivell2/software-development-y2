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

from gameutil import ScalingImageSprite, HookSprite, BoxesTransition, ImageSprite
from consts import VZERO

from gmods import TextureClippingCacheModule, BlueprintsStorageModule, PlayerStateTrackingModule, CardSpawningModule, CameraSpoofingModule
import fonts
import palette

from tooltip import Tooltip
from ui import AbstractButton, NamedButton, ProgressBar, TargettingProgressBar, DodgingProgressBar
from turntaking import PlayerTurnTakingModue


def main_menu():
	game.sprites.purge_preserve("TRANSITION")
	game.sprites.new(ScalingImageSprite(VZERO, game.assets.citiedlow1), layer_override="BACKGROUND")

	def start_game():
		game.loop.run(scenario_choice)
		# game.sprites.new(BoxesTransition(game.windowsystem.rect.copy(), (16, 9), callback = lambda: game.loop.run(mainloop)))

	game.sprites.new(NamedButton(FRect(150, 500, 200, 100), "PLAY", onclick = start_game))
	game.sprites.new(NamedButton(FRect(400, 500, 200, 100), "TUTORIAL"))
	game.sprites.new(NamedButton(FRect(650, 500, 200, 100), "EXIT", onclick = lambda: game.sprites.new(BoxesTransition(game.windowsystem.rect.copy(), (16, 9), callback = game.loop.stop))))

	game.sprites.new(ImageSprite(Vector2(100, 150), game.assets.logo), layer_override="FOREGROUND")


def scenario_choice():
	game.sprites.purge_preserve("TRANSITION", "BACKGROUND")
	game.sprites.new(ScalingImageSprite(VZERO, game.assets.citiedlow1), layer_override="BACKGROUND")

	def start_game(scenario_id):
		game.playerturn.set_scenario_id(scenario_id)
		game.sprites.new(BoxesTransition(game.windowsystem.rect.copy(), (16, 9), callback = lambda: game.loop.run(mainloop)))

	game.sprites.new(ImageSprite(Vector2(200, 150), game.assets.scenarios), layer_override="FOREGROUND")
	button_start = FRect(200, 400, 500, 100)

	for scen_id, scenario in game.blueprints.iscenarios():
		scenario_start = NamedButton(button_start.copy(), scenario["name"].upper(), onclick = functools.partial(start_game, scen_id))
		game.sprites.new(scenario_start)
		game.sprites.new(Tooltip(scenario["name"], scenario["description"], scenario_start.rect, parent = scenario_start))
		button_start.topleft += Vector2(0, 150)

	button_start.width = 200
	game.sprites.new(NamedButton(button_start, "MAIN MENU", onclick = lambda: game.loop.run(main_menu)))

def mainloop():
	game.playerstate.reset()
	game.sprites.purge_preserve("TRANSITION")
	game.sprites.new(ScalingImageSprite(VZERO, game.assets.citiedlow1), layer_override="BACKGROUND")

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
	self.game.camera.update()
	self.game.sprites.update()
	self.game.playerstate.update()
	self.game.debug.update()
	self.game.windowsystem.update()


if __name__ == "__main__":
	game.add_module(
		SpritesManager, layers=["MANAGER", "BACKGROUND", "LOWPARTICLE", "PLAYSPACE", "CARD", "PARTICLE", "FONT", "FOREGROUND", "UI", "TRANSITION"]
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
	game.add_module(CameraSpoofingModule)

	game.loop.functions = SimpleNamespace(gameplay=mainloop, menu=main_menu)
	game.loop.run(main_menu)
