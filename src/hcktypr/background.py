from gamesystem import game
from pygame import Surface, Vector2, Rect, FRect, Color
from gamesystem.common.sprite import Sprite
import random


class MatrixBackgroundRenderer(Sprite):
	LAYER = "BACKGROUND"

	def __init__(self, size, crange=None):
		self._surface = Surface(size)

		self._crange = crange
		if self._crange is None:
			self._crange = Color("#000000"), Color("#004000")

		c1, c2 = self._crange
		self._colours = [c1.lerp(c2, random.uniform(0, 1.0)) for _ in range(10)]

		self._colstate = 0

		self._droplets = []
		for _ in range(10):
			self.spawn_droplet()

	def spawn_droplet(self, pos=None):
		colour = self.get_random_colour() if len(self._droplets) <= 15 else Color("#000000")

		if pos is None:
			# pos = [Vector2(random.randint(0, self._surface.get_width()), self._surface.get_height() - 1), colour]
			pos = [Vector2(random.randint(0, self._surface.get_width()), 0), colour]
			self._droplets.append(pos)

	def get_random_colour(self):
		self._colstate += 1
		if self._colstate > 10:
			self._colstate = 0

		seed = random.randint(0, 100)
		prev = 0

		if isinstance(self._colours, dict):
			for k, v in self._colours.items():
				if k + prev >= seed:
					return v
				prev += k
		elif isinstance(self._colours, list):
			return random.choice(self._colours)

		return Color("#000000")

	def update_move(self):
		if random.randint(0, self._surface.get_height() // 4) == 1 or self._colstate > 8:
			self.spawn_droplet()

		for i in range(len(self._droplets) - 1, -1, -1):
			droplet, _ = self._droplets[i]
			droplet.update(droplet + Vector2(0, 1))

			if droplet.y >= self._surface.get_height(
			) or droplet.y < 0 or droplet.x < 0 or droplet.x >= self._surface.get_width():
				self._droplets.pop(i)

			elif random.randint(0, self._surface.get_height() // 2) == 1:
				pos, c = self._droplets.pop(i)
				pos -= Vector2(0, 1)
				self._droplets.append([pos - Vector2(2, 0), self.get_random_colour()])
				self._droplets.append([pos + Vector2(2, 0), self.get_random_colour()])

	def update_draw(self, to_surface=None):
		self._surface.lock()
		for dpos, dcol in self._droplets:
			dpos = (int(dpos.x), int(dpos.y))
			self._surface.set_at(dpos, dcol)

		self._surface.unlock()

		target = to_surface if to_surface is not None else game.windowsystem.screen
		target.blit(self._surface, (0, 0))


class ScrollingBackgroundRenderer(Sprite):
	LAYER = "BACKGROUND"

	def __init__(self, size, colours=None):
		self._surfaces = [Surface(size) for _ in range(num)]

		self._colours = colours
		if self._colours is None:
			c1, c2 = Color("#076e0f"), Color("#00ff00")

			self._colours = [c1.lerp(c2, random.uniform()) for _ in range(10)]
			self._colours.append(Color("#000000"))

		t = 0
		c = self.get_random_colour()
		for surf in self._surfaces:
			w, h = surf.get_size()
			surf.lock()
			for y in range(h):
				for x in range(w):
					if t == 0:
						t = random.randint(10, w // 4)
						c = self.get_random_colour()
					t -= 1

					surf.set_at((x, y), c)

			surf.unlock()

	def get_random_colour(self):
		seed = random.randint(0, 100)
		prev = 0

		if isinstance(self._colours, dict):
			for k, v in self._colours.items():
				if k + prev >= seed:
					return v
				prev += k
		elif isinstance(self._colours, list):
			return random.choice(self._colours)

		return Color("#000000")

	def update_draw(self):
		game.windowsystem.screen.blit(random.choice(self._surfaces), (0, 0))


class RandomizedBackgroundRenderer(Sprite):
	LAYER = "BACKGROUND"

	def __init__(self, size, num=10, colours=None):
		self._surfaces = [Surface(size) for _ in range(num)]

		self._colours = colours
		if self._colours is None:
			self._colours = {4: Color("#000000"), 30: Color("#013e0f"), 60: Color("#000000"), 2: Color("#008f00")}

		t = 0
		for surf in self._surfaces:
			w, h = surf.get_size()
			surf.lock()
			for y in range(h):
				for x in range(w):
					surf.set_at((x, y), self.get_random_colour())

			surf.unlock()

	def get_random_colour(self):
		seed = random.randint(0, 100)
		prev = 0

		if isinstance(self._colours, dict):
			for k, v in self._colours.items():
				if k + prev >= seed:
					return v
				prev += k
		elif isinstance(self._colours, list):
			return random.choice(self._colours)

		return Color("#000000")

	def update_draw(self):
		game.windowsystem.screen.blit(random.choice(self._surfaces), (0, 0))
