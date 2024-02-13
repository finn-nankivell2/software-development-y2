#!/usr/bin/python3
import pygame
from pygame import Surface, Vector2, Rect, FRect

pygame.init()

import os
import random

from context import gamesystem
from gamesystem import game, GameModule
from gamesystem.mods.input import InputManagerScalingMouse
from gamesystem.mods.window import ScalingWindowSystem, MultiLayerScreenSystem
from gamesystem.mods.defaults import SpritesManager, StateManager, GameloopManager
from gamesystem.mods.debug import DebugOverlayManager

from gamesystem.common.composites import Dimensions
from gamesystem.common.sprite import Sprite
from gamesystem.common.assets import SpriteSheet


class TilemapModule(GameModule):
	IDMARKER = "tilemap"

	def create(self, size, tile_types, tsize=10):
		self.size = Dimensions.try_create(size)
		self._tile_types = tile_types
		self._tiles = [[self.tile("empty") for _ in range(self.size.w())] for _ in range(self.size.h())]
		self._tsize = 10

	def set_from_surface(self, surf, tmap=None):
		tmap = {"empty": (0, 0, 0), "brick": (255, 255, 255)} if tmap is None else tmap
		self.create(surf.get_size(), list(tmap.keys()))

		surf.lock()
		for y in range(self.size.h()):
			for x in range(self.size.w()):
				pos = (x, y)
				c = surf.get_at(pos)
				for k, v in tmap.items():
					if c == v:
						self.set_at(pos, self.tile(k))
		surf.unlock()

	def get_at(self, pos):
		return self._tiles[pos[1]][pos[0]]

	def get_at_or_empty(self, pos):
		if pos[0] < 0 or pos[0] >= self.size.w():
			return 0
		if pos[1] < 0 or pos[1] >= self.size.h():
			return 0
		return self._tiles[pos[1]][pos[0]]

	def get_around(self, pos):
		x, y = pos

		top = self.get_at_or_empty((x, y - 1))
		bot = self.get_at_or_empty((x, y + 1))
		left = self.get_at_or_empty((x - 1, y))
		right = self.get_at_or_empty((x + 1, y))

		return TilemapDirections(top, bot, left, right)

	def set_at(self, pos, tile_val):
		self._tiles[pos[1]][pos[0]] = tile_val

	def get_tiles_array(self):
		return self._tiles

	def tile(self, name):
		return self._tile_types.index(name)

	def get_grid_pos(self, pos):
		x = int(pos[0] * (self._tsize / 100))
		y = int(pos[1] * (self._tsize / 100))
		return (x, y)

	def colliding_tiles(self, rect):
		tl = self.get_grid_pos(rect.topleft)
		br = self.get_grid_pos((rect.x + rect.w - 1, rect.y + rect.h - 1))  # uhhhh

		positions = []
		for y in range(tl[1], br[1] + 1):
			if y < 0 or y >= self.size.h():
				continue

			for x in range(tl[0], br[0] + 1):
				if x < 0 or x >= self.size.w():
					continue
				positions.append([x, y])

		return positions


class TilemapRulesAsset():

	def __init__(self, spritesheet, ruleset):
		self._sheet = spritesheet
		self._ruleset = ruleset

		assert all(k in self._sheet.get_names() for k, _ in ruleset)

	def get_accurate_sheet(self, around):
		for name, rule in self._ruleset:
			if rule.compare(around):
				return self._sheet.get_by_name(name)

		return self._sheet.get_at(0)


class TilemapDirections():

	def __init__(self, top, bottom, left, right, enumval=1):
		self.top = top
		self.bottom = bottom
		self.right = right
		self.left = left
		self._enumval = enumval

	def as_tuple(self):
		return (self.top, self.bottom, self.left, self.right)

	def compare(self, other):

		equality = []
		for s, o in zip(self.as_tuple(), other.as_tuple()):
			(0, 2, 0, 2), (0, 2, 2, 2)
			equality.append(s == o or (s == 0 and o != self._enumval))
		return all(equality)


class AssetNamespace(GameModule):
	IDMARKER = "asset"

	def create(self, sprites):
		for name, path in sprites.items():
			self.__dict__[name] = pygame.image.load(path).convert_alpha()


class TilemapTester(Sprite):
	LAYER = "TILEMAP"

	def __init__(self):
		self._TSIZE = 20

	def _m_rect(self):
		return Rect(*game.input.mouse_pos(), 60, 20)

	def _do_mouse_build(self):
		if game.input.mouse.any():
			pgrid = game.tilemap.get_grid_pos(game.camera.get_mouse_pos_offset())

			if pgrid[0] >= game.tilemap.size.w() or pgrid[0] < 0:
				return
			if pgrid[1] >= game.tilemap.size.h() or pgrid[1] < 0:
				return

			v = game.tilemap.get_at(pgrid)

			if game.input.mouse.LEFT:
				game.tilemap.set_at(pgrid, 1)
			if game.input.mouse.RIGHT:
				game.tilemap.set_at(pgrid, 0)
			if game.input.mouse.MIDDLE:
				game.tilemap.set_at(pgrid, 2)

	def update_move(self):
		self._do_mouse_build()

	def update_draw(self):
		TSIZE = 10

		v1 = game.camera.get_offset((0, 0))
		v2 = Vector2(0, 0)

		for y, col in enumerate(game.tilemap.get_tiles_array()):
			v2.y = y * TSIZE

			for x, cell in enumerate(col):
				v2.x = x * TSIZE

				if cell == 1:
					around = game.tilemap.get_around((x, y))
					use_img = game.asset.tilemap.get_accurate_sheet(around)

					game.screens.layers.main.blit(use_img, v1 + v2)

				if cell == 2:
					around = game.tilemap.get_around((x, y))
					use_img = game.asset.cloudmap.get_accurate_sheet(around)

					game.screens.layers.main.blit(use_img, (v1 + v2))

		pgrid = Vector2(game.tilemap.get_grid_pos(game.camera.get_mouse_pos_offset()))
		p = game.camera.get_offset(pgrid * 10)

		c = (255, 255, 255)

		if pgrid[0] >= game.tilemap.size.w() or pgrid[0] < 0:
			c = (255, 0, 0)
		if pgrid[1] >= game.tilemap.size.h() or pgrid[1] < 0:
			c = (255, 0, 0)

		pygame.draw.rect(game.screens.layers.main, c, (p[0], p[1], 10, 10), 1)


class BackgroundDrawer(Sprite):
	LAYER = "BACKGROUND"

	def __init__(self):
		self._order = []
		for _ in range(random.randint(25, 30)):
			self._order.append(game.asset.sky.rand())

	def update_draw(self):
		TSIZE = 10

		game.debug.output(1 / game.state.deltatime)

		for iy, col in enumerate(game.tilemap.get_tiles_array()):
			y = iy * TSIZE
			if y > game.windowsystem.dimensions.h():
				break

			for ix, cell in enumerate(col):
				x = ix * TSIZE
				if x > game.windowsystem.dimensions.w():
					break

				game.screens.layers.main.blit(self._order[(ix + iy * ix) % len(self._order)], (x, y))


class Player(Sprite):
	LAYER = "PLAYER"

	def __init__(self, rect, colour):
		self.rect = FRect(rect)
		self.c = colour

		self._yvel = 0.0
		self._jump_force = 2.5
		self._speed = 160

		self._left = False

		self._on_ground = True
		self._on_ground_last_frame = False

		self._scales = Vector2(1.0, 1.0)
		self._scales_follower = Vector2(1.0, 1.0)  # This is what's actually used

		# self._scales = Vector2(1.0, 1.0)

	def _on_ground_check(self):
		return any(
			game.tilemap.get_at(pos) in (1, 2)
			for pos in game.tilemap.colliding_tiles(Rect(*self.rect.bottomleft, self.rect.w, 2))
		)

	def _update_physics(self, movement):
		oldx, oldy = self.rect.topleft

		self.rect.x += movement.x * self._speed * game.state.deltatime

		collides = game.tilemap.colliding_tiles(self.rect)
		for pos in collides:
			g = game.tilemap.get_at(pos)
			if g in (1, 2):
				self.rect.x = oldx

		self.rect.y += movement.y * self._speed * game.state.deltatime

		collides = game.tilemap.colliding_tiles(self.rect)
		for pos in collides:
			g = game.tilemap.get_at(pos)

			oldyvel = self._yvel
			if g in (1, 2):
				self._yvel = 0
				self.rect.y = oldy

				if not self._on_ground:
					self._on_ground = True
					self._scales.x = 1.8
					self._scales.y = 0.2

			elif not self._on_ground_check():
				self._on_ground = False
				self._scales.x = 0.8
				self._scales.y = 1.2

			if g == 2:
				if self.rect.centery < pos[1] * 10:
					self._yvel = -2
					self.rect.y += self._yvel

		# if self.rect.right < 0:
		# 	self.rect.left = game.windowsystem.dimensions.w()

		# if self.rect.left > game.windowsystem.dimensions.w():
		# 	self.rect.left = 0

		# if self.rect.top > game.windowsystem.dimensions.h():
		# 	self.rect.bottom = 0

	def update_move(self):
		move = Vector2(0, 0)

		if game.input.key_down(pygame.K_LEFT) or game.input.key_down(pygame.K_a):
			move.x -= 1
			self._left = True
		if game.input.key_down(pygame.K_RIGHT) or game.input.key_down(pygame.K_d):
			move.x += 1
			self._left = False

		if game.input.key_pressed(pygame.K_SPACE):
			self._yvel = -self._jump_force

		if game.input.key_pressed(pygame.K_r):
			self.rect.topleft = (0, 0)
			self._yvel = 0

		if game.input.key_pressed(pygame.K_x):
			self.destroy()

		self._yvel += 10 * game.state.deltatime
		if self._yvel > 10:
			self._yvel = 10

		move.y += self._yvel
		self._update_physics(move)
		self._update_camera()

	def _update_camera(self):
		oldpos = (game.camera.pos.x, game.camera.pos.y)

		camera_move = (Vector2(self.rect.center) - game.windowsystem.dimensions // 2) - game.camera.pos
		game.camera.pos.x += camera_move.x

		x = game.camera.pos.x
		xw = game.camera.pos.x + game.camera.size.w()

		if x < 0:
			game.camera.pos.x = 0
		elif xw >= game.tilemap.size.w() * 10:
			game.camera.pos.x = game.tilemap.size.w() * 10 - game.camera.size.w()

		game.camera.pos.y += camera_move.y

		y = game.camera.pos.y
		yw = game.camera.pos.y + game.camera.size.h()

		if y < 0:
			game.camera.pos.y = 0
		elif yw >= game.tilemap.size.h() * 10:
			game.camera.pos.y = game.tilemap.size.h() * 10 - game.camera.size.h()

		RATE = 0.05
		self._scales = self._scales.move_towards(Vector2(1.0, 1.0), RATE)
		self._scales_follower = self._scales_follower.move_towards(self._scales, RATE * 4)

	def update_draw(self):
		pos = game.camera.get_offset(self.rect.midbottom)

		use_img = game.asset.player

		if self._left:
			use_img = pygame.transform.flip(use_img, True, False)

		use_img = pygame.transform.scale_by(use_img, self._scales_follower)

		pos[0] -= use_img.get_width() / 2
		pos[1] -= use_img.get_height()

		game.screens.layers.main.blit(use_img, pos)


class CameraManager(GameModule):
	IDMARKER = "camera"
	REQUIREMENTS = ["windowsystem", "input"]

	def create(self):
		self.pos = Vector2(0, 0)
		self.size = game.windowsystem.dimensions

	def get_mouse_pos_offset(self):
		return self.pos + self.game.input.mouse_pos()

	def get_offset(self, ofs):
		return Vector2(ofs) - self.pos

	def update(self):
		pass


def do_running(self):
	self.game.state.update()
	self.game.input.update()
	self.game.sprites.update()
	self.game.screens.update()
	self.game.debug.update()
	self.game.windowsystem.update()


def mainloop():
	surf = Surface((32 * 4, 18 * 4))
	surf.fill((0, 0, 0))

	pygame.draw.rect(surf, (255, 255, 255), (20, 13, 10, 5))

	pygame.draw.rect(surf, (255, 255, 255), (5, 9, 10, 5))

	game.tilemap.set_from_surface(surf, tmap={"empty": (0, 0, 0), "brick": (255, 255, 255), "cloud": (0, 0, 255)})
	game.sprites.new(TilemapTester())

	game.spriteglobals.PLAYER = Player(FRect(120, 20, 12, 18), (255, 255, 255))

	game.sprites.new(game.spriteglobals.PLAYER)
	game.sprites.new(BackgroundDrawer())


game.add_module(SpritesManager, layers=["BACKGROUND", "TILEMAP", "PLAYER", "FOREGROUND", "UI"])
game.add_module(GameloopManager, loop_hook=do_running)
game.add_module(StateManager)
game.add_module(ScalingWindowSystem, size=Dimensions(320, 180), user_size=Dimensions(1280, 720), caption="gaming")
game.add_module(
	MultiLayerScreenSystem,
	size=Dimensions(320, 180),
	num_layers=4,
	layer_names=["background", "main", "foreground", "ui"]
)
game.add_module(InputManagerScalingMouse)
game.add_module(TilemapModule, size=[1, 1], tile_types=["empty", "brick", "cloud"])
game.add_module(DebugOverlayManager, fontcolour=(255, 255, 255))
game.add_module(CameraManager)
game.add_module(
	AssetNamespace,
	sprites={
	"tilemap": "sprites/tilemap.png",
	"cloudmap": "sprites/cloudmap.png",
	"sky": "sprites/sky.png",
	"player": "sprites/player.png",
	}
)


def create_normal_platform_tilemap_ruleset(tilemap, e):
	return TilemapRulesAsset(
		tilemap,
		[
		("TOPLEFT", TilemapDirections(0, e, 0, e, enumval=e)),
		("TOPMID", TilemapDirections(0, e, e, e, enumval=e)),
		("TOPRIGHT", TilemapDirections(0, e, e, 0, enumval=e)),
		("MIDLEFT", TilemapDirections(e, e, 0, e, enumval=e)),
		("MIDMID", TilemapDirections(e, e, e, e, enumval=e)),
		("MIDRIGHT", TilemapDirections(e, e, e, 0, enumval=e)),
		("BOTLEFT", TilemapDirections(e, 0, 0, e, enumval=e)),
		("BOTMID", TilemapDirections(e, 0, e, e, enumval=e)),
		("BOTRIGHT", TilemapDirections(e, 0, e, 0, enumval=e)),
		("TOPSING", TilemapDirections(0, e, 0, 0, enumval=e)),
		("RIGHTSING", TilemapDirections(0, 0, e, 0, enumval=e)),
		("LEFTSING", TilemapDirections(0, 0, 0, e, enumval=e)),
		("BOTSING", TilemapDirections(e, 0, 0, 0, enumval=e)),
		("SING", TilemapDirections(0, 0, 0, 0, enumval=e)),
		("MIDSING", TilemapDirections(0, 0, e, e, enumval=e)),
		("MIDMID", TilemapDirections(e, e, 0, 0, enumval=e)),
		]
	)


game.asset.sky = SpriteSheet(game.asset.sky, Dimensions(10, 10))
game.asset.tilemap = SpriteSheet(
	game.asset.tilemap,
	Dimensions(10, 10),
	names=[
	"TOPLEFT",
	"TOPMID",
	"TOPRIGHT",
	"MIDLEFT",
	"MIDMID",
	"MIDRIGHT",
	"BOTLEFT",
	"BOTMID",
	"BOTRIGHT",
	"TOPSING",
	"RIGHTSING",
	"LEFTSING",
	"BOTSING",
	"SING",
	"MIDSING"
	]
)
game.asset.tilemap = create_normal_platform_tilemap_ruleset(game.asset.tilemap, 1)

game.asset.cloudmap = SpriteSheet(
	game.asset.cloudmap,
	Dimensions(10, 10),
	names=[
	"TOPLEFT",
	"TOPMID",
	"TOPRIGHT",
	"MIDLEFT",
	"MIDMID",
	"MIDRIGHT",
	"BOTLEFT",
	"BOTMID",
	"BOTRIGHT",
	"TOPSING",
	"RIGHTSING",
	"LEFTSING",
	"BOTSING",
	"SING",
	"MIDSING"
	]
)
game.asset.cloudmap = create_normal_platform_tilemap_ruleset(game.asset.cloudmap, 2)

game.loop.run(mainloop)
