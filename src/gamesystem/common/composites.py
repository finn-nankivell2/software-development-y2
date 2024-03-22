from pygame import Vector2
from .typechecking import is_2size_tuple
import random

from dataclasses import dataclass

__all__ = ["MouseState"]


class MouseState():
	__slots__ = ["LEFT", "RIGHT", "MIDDLE"]

	def __init__(self, mouse_state=(False, False, False)):
		self.alter(mouse_state)

	def items(self):
		return (self.LEFT, self.MIDDLE, self.RIGHT)

	def __getitem__(self, index):
		if index > 2:
			raise IndexError("Index must not be more than 2")

		if index == 0:
			return self.LEFT
		if index == 1:
			return self.RIGHT
		if index == 2:
			return self.MIDDLE

	def alter(self, mouse_state):
		self.LEFT, self.MIDDLE, self.RIGHT = [bool(m) for m in mouse_state]

	def copy(self):
		return MouseState(self.items())

	def any(self):
		return self.LEFT or self.MIDDLE or self.RIGHT

	def __repr__(self):
		return f"MouseState({self.LEFT}, {self.RIGHT}, {self.MIDDLE})"
