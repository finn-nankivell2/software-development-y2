from .modulebase import GameModule
from ..common.composites import MouseState

from pygame.math import Vector2
import pygame.key
import pygame.mouse


class InputManager(GameModule):
	"""GameModule for handling mouse and keyboard input"""

	IDMARKER = "input"
	REQUIREMENTS = ["windowsystem"]

	def create(self):
		"""Create InputManager"""
		self.keys = []
		self._last_keys = []

		self.mouse = MouseState()
		self._last_mouse = MouseState()

		self._mouse_pos = Vector2(0, 0)
		self._last_mouse_pos = Vector2(0, 0)
		self._mouse_rel = Vector2(0, 0)

		self._freeze_input = False

	def freeze(self, v=True):
		"""Freeze InputManager so that keys cant be read"""
		self._freeze_input = v

	def update(self):
		"""Update InputManager state"""
		self._last_keys = self.keys
		self.keys = pygame.key.get_pressed()

		self._last_mouse = self.mouse.copy()
		self.mouse = MouseState(pygame.mouse.get_pressed())

		self._mouse_pos_last = self._mouse_pos
		self._mouse_pos = Vector2(pygame.mouse.get_pos())
		self._mouse_rel = Vector2(pygame.mouse.get_rel())

	def mouse_pos(self):
		"""Get mouse position"""
		return self._mouse_pos

	def mouse_movement(self):
		"""Get mouse movement change since last frame"""
		return self._mouse_rel

	def key_down(self, key_code):
		"""Check if key is down"""
		return self.keys[key_code] and not self._freeze_input

	def key_pressed(self, key_code):
		"""Check if key is pressed on this frame only"""
		return self.keys[key_code] and not self._last_keys[key_code] and not self._freeze_input

	def mouse_down(self, idx):
		"""Check if mouse is down"""
		return self.mouse[idx] and not self._freeze_input

	def mouse_pressed(self, idx):
		"""Check if mouse is pressed on this frame only"""
		return self.mouse[idx] and not self._last_mouse[idx] and not self._freeze_input


class InputManagerScalingMouse(InputManager):
	REQUIREMENTS = ["scalingwindowsystem"]

	def update(self):
		"""Add to default update behaviour so that the mouse position accounts for the window scaling

		Requires a ScalingWindowSystem to be initialized
		"""
		super().update()

		mp = self._mouse_pos
		scale = self.game.windowsystem.scale_down
		self._mouse_pos = Vector2(mp.x * scale.x, mp.y * scale.y)

		mr = self._mouse_rel
		self._mouse_rel = Vector2(mr.x * scale.x, mr.y * scale.y)


def test_UNIT_mousestate():
	m1 = MouseState()
	m2 = m1.copy()

	assert m1 is not m2

	m1.alter((True, False, False))
	assert m1.LEFT is True
