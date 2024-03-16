import random
import math
from gamesystem.common.sprite import Sprite, SpriteGroup
from gamesystem import game
import pygame
from pygame import Vector2, Color, Surface, FRect, Rect
from typing import List, Union, Iterator, Tuple, Callable


class Particle(Sprite):
	LAYER = "PARTICLE"

	def __init__(self, pos, size, vel, colour, lifetime=60):
		self.pos = pos
		self.size = size
		self.vel = vel
		self.colour = colour
		self.outline = self.colour.lerp(Color("#ffffff"), 0.5)
		self._decay = self.size / lifetime

	@classmethod
	def rand_angle(cls, *args, speed=5, **kwargs):
		a = random.randint(0, 359)
		kwargs["vel"] = Vector2(math.cos(a), math.sin(a)) * speed
		return cls(*args, **kwargs)

	def update_move(self):
		self.pos += self.vel
		self.size -= self._decay
		if self.size < 1:
			self.destroy()

	def update_draw(self):
		pygame.draw.circle(game.windowsystem.screen, self.colour, self.pos, self.size)


def particle_explosion(number, *args, **kwargs) -> List[Particle]:
	parts = []
	for _ in range(number):
		if kwargs.get("speed"):
			kwargs["speed"] *= random.uniform(0.6, 1.4)
		else:
			kwargs["speed"] = random.randint(3, 10)

		parts.append(Particle.rand_angle(*args, **kwargs))

	return parts


class FollowParticle(SpriteGroup):
	LAYER = "BACKGROUND"

	def __init__(self, pos=Vector2(0, 0), colours=["#923efc", "#6e1698"], mouse_follow=False):
		super().__init__()

		self.pos = pos
		colours = list(map(Color, colours))
		self.c1, self.c2 = colours
		self.mouse_follow = mouse_follow

	def update_move(self):
		a = random.randint(0, 180)
		vel = Vector2(math.cos(a), math.sin(a))

		c = self.c1.lerp(self.c2, random.uniform(0.0, 1.0))
		part = Particle(
			Vector2(self.pos),
			95,
			vel,
			c,
			lifetime=1120 + random.randint(-50, 50),
		)

		if self.mouse_follow:
			self.pos = game.input.mouse_pos()
			if game.input.mouse_down(0):
				self.sprites.append(part)
		else:
			self.sprites.append(part)

		super().update_move()

	def update_draw(self):
		game.debug.output(len(self.sprites))

		for part in reversed(self.sprites):
			pygame.draw.circle(game.windowsystem.screen, part.outline, part.pos, part.size + 6)

		for part in reversed(self.sprites):
			pygame.draw.circle(game.windowsystem.screen, part.colour, part.pos, part.size)
