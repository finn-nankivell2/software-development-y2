from gamesystem.common.sprite import Sprite, SpriteGroup
from gamesystem import game
import pygame
import random
import math
from pygame import Vector2, Color, Surface, FRect, Rect
from typing import List, Union, Iterator, Tuple, Callable, Any
from consts import VZERO
from utils import first


def surface_keepmask(surface: Surface, masking: Callable[[Surface, Color], Any]) -> Surface:
	dest = Surface(surface.get_size(), pygame.SRCALPHA)
	dest2 = Surface(surface.get_size(), pygame.SRCALPHA)
	dest.blit(surface, VZERO)

	MASK_BG = Color("#ff00ff")
	MASK_FG = Color("#ff0000")

	mask = Surface(surface.get_size())
	mask.fill(MASK_BG)
	masking(mask, MASK_FG)
	mask.set_colorkey(MASK_FG)

	dest.blit(mask, VZERO)
	dest.set_colorkey(MASK_BG)

	dest2.blit(dest, VZERO)

	return dest2


def surface_rounded_corners(surface: Surface, corner_radius: int) -> Surface:
	return surface_keepmask(
		surface, lambda surf, col: pygame.draw.rect(surf, col, surf.get_rect(), border_radius=corner_radius)
	)


def shadow_from_rect(rect: Rect, colour: Color = Color("#000000aa"), shrink_by=10, blur_radius=8, **kwargs) -> Surface:
	surf = Surface(rect.size, pygame.SRCALPHA)
	pygame.draw.rect(surf, colour, rect.inflate(-shrink_by, -shrink_by), **kwargs)
	return pygame.transform.gaussian_blur(surf, blur_radius)


def traverse_surface(surface: Surface) -> Iterator[Tuple[int, int]]:
	w, h = surface.get_size()

	for y in range(h):
		for x in range(w):
			yield (x, y)


def transmute_surface_palette(surface: Surface, palette_map: List[Tuple[Color, Color]]) -> Surface:
	surface.lock()
	for pos in traverse_surface(surface):
		c = surface.get_at(pos)
		newc = first(nc for k, nc in palette_map if k == c)
		if newc:
			surface.set_at(pos, newc)

	surface.unlock()
	return surface


def surface_region(surface: Surface, region: Union[Rect, FRect]) -> Surface:
	target = Surface(region.size, pygame.SRCALPHA)
	target.blit(surface, (0, 0), region)
	return target


class ImageSprite(Sprite):

	def __init__(self, pos: Vector2, image: Surface):
		self.pos = pos
		self.image = image

	def update_draw(self):
		game.windowsystem.screen.blit(self.image, self.pos)


class ScalingImageSprite(ImageSprite):

	def __init__(self, pos: Vector2, image: Surface):
		super().__init__(pos, image)
		self.unscaled = self.image
		self.image = pygame.transform.scale(self.unscaled, game.windowsystem.dimensions)


__all__ = [
	traverse_surface.__name__,
	transmute_surface_palette.__name__,
	surface_region.__name__,
	surface_keepmask.__name__,
	surface_rounded_corners.__name__,
	ImageSprite.__name__,
	ScalingImageSprite.__name__
]
