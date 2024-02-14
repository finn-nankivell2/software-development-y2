from pygame import Surface, SRCALPHA, Rect
from typing import List, Tuple

import random

__all__ = ["SpriteSheet"]


class SpriteSheet():

	def __init__(self, src: Surface, dimensions: Tuple[int, int], names: List[str] = None):
		self._sheet = src
		self._src_dims = src.get_size()
		self._dims = dimensions

		if self._src_dims[0] % self._dims[0] != 0 or self._src_dims[1] % self._dims[1] != 0:
			raise ValueError(f"Given dimensions {self._dims} do not fit into sheet dimensions {self._src_dims}")

		self._sprites = []
		for y in range(0, self._src_dims[1], self._dims[1]):
			for x in range(0, self._src_dims[0], self._dims[0]):
				surf = Surface(self._dims, SRCALPHA)

				r = Rect(x, y, self._dims[0], self._dims[1])

				surf.blit(self._sheet, (0, 0), r)
				self._sprites.append(surf)

		if names is not None:
			self.add_names(names)

	def add_names(self, names: List[str]):
		self._names = names

		if type(self._names) is not list:
			raise ValueError("Names must be a list")

		if not all(type(t) is str for t in self._names):
			raise ValueError("Names must all be strings")

		if len(self._names) != len(self._sprites):
			raise ValueError(f"Name length ({len(self._names)}) differs to sprite length ({len(self._sprites)})")

		for n, spr in zip(self._names, self._sprites):
			if n.startswith("_"):
				continue
				# raise ValueError("Sprite names must not start with an underscore")
			self.__dict__[n] = spr

	def get_at(self, idx: int) -> Surface:
		return self._sprites[idx]

	def get_by_name(self, name: str):
		return self.__dict__[name]

	def get_names(self) -> List[str]:
		return self._names

	def __getitem__(self, idx: int):
		return self._sprites[idx]

	def __len__(self) -> int:
		return len(self._sprites)

	def rand(self) -> Surface:
		return random.choice(self._sprites)

	def dimensions(self) -> Tuple[int, int]:
		return self._dims

	def pseudorand(self, seed) -> Surface:
		return self._sprites[seed % len(self)]


def test_UNIT_spritesheet_creation():
	src = Surface((1000, 100))
	src.fill((0, 0, 0))

	sheet = SpriteSheet(src, Dimensions(500, 100), ["hehe", "haha"])
