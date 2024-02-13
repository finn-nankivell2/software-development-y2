#!/usr/bin/python3
import pygame
from pygame import Surface, Vector2, Rect, FRect, Color

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

from gamesystem.common.sprite import Sprite
from gamesystem.common.assets import SpriteSheet


class DrawRect(Sprite):
	LAYER = "BACKGROUND"

	def __init__(self):
		pass

	def update_draw(self):
		pygame.draw.rect(game.windowsystem.screen, Color("#f74596"), (10, 10, 20, 20))


def do_running(self):
	self.game.state.update()
	self.game.input.update()
	self.game.sprites.update()
	game.debug.output(1 / game.state.deltatime)
	self.game.debug.update()
	self.game.windowsystem.update()


def mainloop():
	game.sprites.new(DrawRect())


game.add_module(SpritesManager, layers=["BACKGROUND", "BULLET", "PLAYER", "FOREGROUND", "UI"])
game.add_module(GameloopManager, loop_hook=do_running)
game.add_module(StateManager)
game.add_module(
	ScalingWindowSystem,
	size=Vector2(320, 180),
	user_size=Vector2(1280, 720),
	caption="Bullet Stress Test",
	flags=pygame.NOFRAME,
	fill_color=Color(255, 255, 255)
)
game.add_module(InputManagerScalingMouse)
game.add_module(DebugOverlayManager, fontcolour=(255, 255, 255))

game.loop.run(mainloop)
