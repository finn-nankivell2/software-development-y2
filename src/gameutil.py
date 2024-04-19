from gamesystem.common.sprite import Sprite, SpriteGroup
from gamesystem import game
import pygame
import random
import math
from pygame import Vector2, Color, Surface, FRect, Rect
from typing import List, Union, Iterator, Tuple, Callable, Any, Optional
from consts import VZERO
from dataclasses import dataclass
import palette
import requests
import threading
import time

from easing_functions import CubicEaseInOut, BackEaseInOut


# Attempt at a multithreaded client request (does not work due to python3 GIL)
class Promise:
	def __init__(self, method: Callable, url: str, **kwargs):
		self._method = method
		self._url = url
		self._request_kwargs = kwargs
		self.complete = False
		self.response = None

		self._thread = threading.Thread(target=self.target, daemon=True)

	def start(self):
		time.sleep(5)
		self._thread.start()
		return self

	def target(self):
		self.response = self._method(self._url, **self._request_kwargs)
		self.complete = True


# Layer of abstraction over both a Vector2 and an easing function
class EasingVector2:

	def __init__(self, start: Vector2, end: Vector2, func=CubicEaseInOut, duration: int = 30):
		self.start = Vector2(start)
		self.end = Vector2(end)
		self.func = func
		self.duration = duration

		self.xfunc = func(self.start.x, self.end.x, duration)
		self.yfunc = func(self.start.y, self.end.y, duration)

	def __call__(self, alpha):
		return Vector2(self.xfunc(alpha), self.yfunc(alpha))

	def ease(self, alpha):
		return self(alpha)


# EasingVector2 that handles the alpha increments itself
class SteppingEasingVector2(EasingVector2):

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._step = 0

	def completed(self):
		return self._step >= self.duration

	def step(self):
		self._step += 1
		return self(self._step)


# Apply a draw function to a Surface, and mask out the drawn on areas
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


# Give a surface rounded corners
def surface_rounded_corners(surface: Surface, corner_radius: int) -> Surface:
	return surface_keepmask(
		surface, lambda surf, col: pygame.draw.rect(surf, col, surf.get_rect(), border_radius=corner_radius)
	)


# Generate a blurry shadow Surface given a Rect
def shadow_from_rect(rect: Rect, colour: Color = Color("#000000aa"), shrink_by=10, blur_radius=8, **kwargs) -> Surface:
	surf = Surface(rect.size, pygame.SRCALPHA)
	pygame.draw.rect(surf, colour, rect.inflate(-shrink_by, -shrink_by), **kwargs)
	return pygame.transform.gaussian_blur(surf, blur_radius)


# Iterate over every coordinate in a Surface
def traverse_surface(surface: Surface) -> Iterator[Tuple[int, int]]:
	w, h = surface.get_size()

	for y in range(h):
		for x in range(w):
			yield (x, y)


# Change a Surface's palette to a set of new colours
def transmute_surface_palette(surface: Surface, palette_map: List[Tuple[Color, Color]]) -> Surface:
	surface.lock()
	for pos in traverse_surface(surface):
		c = surface.get_at(pos)
		newc = next((nc for k, nc in palette_map if k == c), None)
		if newc:
			surface.set_at(pos, newc)

	surface.unlock()
	return surface


# Get a region of a Surface defined by a Rect
def surface_region(surface: Surface, region: Union[Rect, FRect]) -> Surface:
	target = Surface(region.size, pygame.SRCALPHA)
	target.blit(surface, (0, 0), region)
	return target


# Sprite that renders a given Surface every frame at a given position
class ImageSprite(Sprite):

	def __init__(self, pos: Vector2, image: Surface):
		self.pos = pos
		self.image = image

	def update_draw(self):
		game.windowsystem.screen.blit(self.image, self.pos)


# Extension of ImageSprite that also upscales the image to the window size
class ScalingImageSprite(ImageSprite):

	def __init__(self, pos: Vector2, image: Surface):
		super().__init__(pos, image)
		self.unscaled = self.image
		self.image = pygame.transform.scale(self.unscaled, game.windowsystem.dimensions)


# Extension of the ScalingImageSprite that also renders a scanline effect on top of the image, darkening it and creating an optical illusion
class ScanlineImageSprite(ScalingImageSprite):

	def __init__(self, *args, scans_clr=Color("#000000"), **kwargs):
		super().__init__(*args, **kwargs)
		self.image = ScanlineImageSprite._render_scans(self.image.copy(), scans_clr)

	@staticmethod
	def _render_scans(surface: Surface, clr: Color) -> Surface:
		w = surface.get_width()
		for y in range(surface.get_height()):
			if y % 2 == 0:
				pygame.draw.line(surface, clr, (0, y), (w - 1, y))

		return surface


# Sprite that runs a callback every frame
class HookSprite(Sprite):

	def __init__(self, update_move=None, update_draw=None):
		self.update_move = update_move if update_move is not None else lambda: None
		self.update_draw = update_draw if update_draw is not None else lambda: None



# Transition effect that creates little boxes that fill the screen, using easing functions to make it smoother. Optionally runs a callback to change the scene at the halfway point
class BoxesTransition(Sprite):
	LAYER = "TRANSITION"

	# Internal representation of a box wiping across a portion of the screen
	@dataclass
	class Box:
		pos: Vector2
		start: Vector2
		lifetime: int
		fullwidth: float
		func: BackEaseInOut
		width: float = 0
		tick: int = 0
		diminshing: bool = False

		def update(self):
			self.tick += 1

			# Should grow if not diminishing, shrink if diminishing
			if self.diminshing:
				self.pos.x = self.func(self.tick)
				self.width = self.fullwidth - (self.pos.x - self.start.x)
			else:
				self.width = self.func(self.tick)

		def complete(self):
			if self.diminshing:
				return self.width <= 0

			return self.tick >= self.lifetime

	def __init__(self, rect: FRect, chunks: Tuple[int, int], colour: Color = palette.BLACK, lifetime=60, callback: Optional[Callable] = None):
		self.rect = rect
		self.boxes = []
		self._lifetime = lifetime
		self._frames = 0
		self._callback = callback
		self._halfway = False
		self.colour = colour

		ch_x, ch_y = chunks
		self._box_width = self.rect.width/ch_x
		self._box_height = self.rect.height/ch_y

		# Create a number of Boxes equal to chunks[0] * chunks[1]
		for i in range(ch_y):
			y = i * self._box_height

			x_offset = 20 * (i % 2)

			for j in range(ch_x + i % 2):
				x = j * self._box_width

				lf = self._lifetime - random.randint(0, self._lifetime/2)
				self.boxes.append(BoxesTransition.Box(
					Vector2(x - x_offset, y),
					Vector2(x - x_offset, y),
					lf,
					self._box_width,
					BackEaseInOut(0, self._box_width, lf)
				))

	# Update all Boxes
	def update_move(self):
		for box in self.boxes:
			box.update()

		# If every Box is complete, begin shrinking them, and run the callback
		if all(b.complete() for b in self.boxes):
			if self._halfway:
				self.destroy()
			else:
				self._callback()
				self._halfway = True

				for box in self.boxes:
					box.diminshing = True
					box.func = BackEaseInOut(box.pos.x, box.pos.x + box.width, box.lifetime)
					box.tick = 0

	# Draw all boxes
	def update_draw(self):
		for box in self.boxes:
			pygame.draw.rect(game.windowsystem.screen, self.colour, (box.pos.x, box.pos.y, box.width, self._box_height+1))



# Module exports
__all__ = [
	traverse_surface.__name__,
	transmute_surface_palette.__name__,
	surface_region.__name__,
	surface_keepmask.__name__,
	surface_rounded_corners.__name__,
	ImageSprite.__name__,
	ScalingImageSprite.__name__,
	EasingVector2.__name__,
	SteppingEasingVector2.__name__,
	BoxesTransition.__name__
]
