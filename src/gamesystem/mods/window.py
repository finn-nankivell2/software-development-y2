"""
GameModules for handling pygame windowing and rendering targets
"""

import pygame
from pygame import Surface, Vector2, Color

import sys
from .modulebase import GameModule
from types import SimpleNamespace


class BasicWindowSystem(GameModule):
	"""A GameModule that creates and manages a pygame window"""

	IDMARKER = "windowsystem"
	REQUIREMENTS = ["loop"]

	def create(self, size: Vector2, caption="pygame window", flags=pygame.SHOWN, fill_color=Color(0, 0, 0)):
		"""Create the window from a size. Optionally set the caption, pygame flags, and fill color"""

		self.dimensions = Vector2(size)
		self.window = pygame.display.set_mode(size, flags)
		self.screen = self.window

		self.game.globals.window = self.window
		# self.game.window = self.window

		pygame.display.set_caption(caption)
		self._bgc = fill_color

	def set_fill_color(self, fill_color: Color):
		"""Set the background fill color"""
		self._bgc = fill_color

	def update(self):
		"""Update the window's buffer and handle close events"""
		pygame.display.flip()
		self.window.fill(self._bgc)

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
				sys.exit()


class ScalingWindowSystem(BasicWindowSystem):
	"""A window system that scales a Surface to fit the window size"""

	ALIASES = ["scalingwindowsystem"]

	def create(self, size, user_size, **kwargs):
		"""Create the window. size defines the Surface size, user_size defines the window size.
		kwargs are passed to BasicWindowSystem.__init__
		"""

		super().create(user_size, **kwargs)  # MUST run super().create() first!

		self.screen = Surface(size, pygame.SRCALPHA)
		self.uscreen = Surface(user_size, pygame.SRCALPHA)

		self.dimensions = Vector2(size)

		self.udimensions = Vector2(user_size)
		# self.game.screen = self.screen
		self.game.globals.screen = self.screen

		self.scale_up = Vector2(self.udimensions.x / self.dimensions.x, self.udimensions.y / self.dimensions.y)
		self.scale_down = Vector2(self.dimensions.x / self.udimensions.x, self.dimensions.y / self.udimensions.y)

	def update(self):
		"""Update the window buffer and events.
		The Surface is scaled to the size of self.udimensions before being blitted
		"""

		t = pygame.transform.scale(self.screen, self.udimensions)
		self.window.blit(t, (0, 0))  # Decide on where to blit later
		self.window.blit(self.uscreen, (0, 0))

		pygame.display.flip()
		self.screen.fill((0, 0, 0, 0))
		self.uscreen.fill((0, 0, 0, 0))
		self.window.fill(self._bgc)

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
				sys.exit()


class MultiLayerScreenSystem(GameModule):
	"""Screen system with multiple different layers to render to.

	Layers are combined together to create one Surface.

	The module does not handle a pygame window, and it requires that a windowsystem module is already initialized
	"""

	IDMARKER = "screens"
	REQUIREMENTS = ["windowsystem"]

	class SurfaceLayer(Surface):
		"""Internal class for managing different layers and their offsets"""

		def __init__(self, *args, **kwargs):
			"""Create a SurfaceLayer with a default offset of (0, 0).

			Uses all the same arguments as a normal Surface
			"""
			super().__init__(*args, **kwargs)
			self._offset = Vector2(0, 0)

		def get_offset(self):
			"""Get the layer's offset"""
			return self._offset

		def set_offset(self, ofs):
			"""Set the layer's offset"""
			self._offset = Vector2(ofs)

	def create(self, size: Vector2, num_layers: int, layer_names=[]):
		"""Create the MultiLayerScreenSystem.

		num_layers refers to the number of surfaces that will be created.

		layer_names is an optional list of strings. If a value is passed then properties corresponding to the string names will be inserted into the MultiLayerScreenSystem's __dict__ attribute and will be more easily accessible
		"""

		self.dimensions = Vector2(size)
		self.num_layers = num_layers
		self._screen = Surface(size, pygame.SRCALPHA)

		self._layer_list = []
		for _ in range(num_layers):
			self._layer_list.append(MultiLayerScreenSystem.SurfaceLayer(size, pygame.SRCALPHA))

		if layer_names:
			assert len(layer_names) == len(self._layer_list)
			assert all(type(t) is str for t in layer_names)

			self.layers = SimpleNamespace()
			for k, v in zip(layer_names, self._layer_list):
				self.layers.__dict__[k] = v

	def update(self):
		"""Combine all layers into one"""
		for layer in self._layer_list:
			self._screen.blit(layer, layer.get_offset())
			layer.fill((0, 0, 0, 0))
		self.game.windowsystem.screen.blit(self._screen, (0, 0))

		assert self.game.windowsystem.dimensions == self.dimensions
		self._screen.fill((0, 0, 0, 0))

	def get_layer(self, idx):
		"""Get a layer from an index"""
		return self._layer_list[idx]

	def __len__(self):
		"""Return the total number of layers"""
		return self.num_layers
