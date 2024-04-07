from .baseclass import BaseSpriteManager
from collections import OrderedDict
from .modulebase import GameModule


class SpritesManager(BaseSpriteManager):
	"""GameModule for managing sprites

	A Sprite is any class that inhreits from gamesystem.commom.sprite.Sprite and has a static LAYER attribute

	The SpritesManager uses multiple layers to manage sprite order of events
	"""

	IDMARKER = "sprites"

	def create(self, layers):
		"""Create a SpritesManager with given layer names

		Also adds a SpriteGlobalsManager for managing aliases to specific important sprites
		"""

		self._sprites = OrderedDict()
		for k in layers:
			self._sprites[k] = []

		self.game.add_module(SpriteGlobalsManager)

	def new(self, new_sprite, layer_override=None):
		"""Add a new sprite to its assigned layer.
		If a string is passed for layer_override the use that value instead of Sprite.LAYER
		"""
		if layer_override is not None:
			self._sprites[layer_override].insert(0, new_sprite)
		else:
			self._sprites[new_sprite.LAYER].insert(0, new_sprite)

	def news(self, *new_sprites, layer_override=None):
		for sprite in new_sprites:
			self.new(sprite, layer_override)

	def layer_names(self):
		"""Return a list of layer names"""
		return self._sprites.keys()

	def add_layer(self, layer_name):
		"""Add a new layer to the SpritesManager. Layer cannot already exist"""
		if layer_name in self.layer_names():
			raise KeyError(f"Layer '{layer_name}' cannot be created as it already exists")

		self._sprites[layer_name] = []

	def get(self, layer_name):
		"""Get a layer of sprites"""
		return list(filter(lambda s: not s.is_destroyed(), self._sprites[layer_name]))

	def purge(self, *layer_names):
		"""Delete all sprites from layers

		If nothing is passed for layer_names then delete all layers. Otherwise delete only the specified layers
		"""
		if not layer_names:
			self.purge(*self.layer_names())

		else:
			for x in layer_names:
				for sprite in self._sprites[x]:
					sprite.destroy()
				self._sprites[x] = []

	def purge_preserve(self, *preserve):
		"""Purge all layers NOT passed in preserve"""
		self.purge(*[x for x in self.layer_names() if x not in preserve])

	def __len__(self):
		"""Get the total number of sprites"""
		return sum(len(x) for x in self._sprites.values())

	def update(self):
		"""Update all sprites in the SpritesManager

		Updating involves
		- Iterating over all layers
		- Iterating over each sprite in the layer
		- Checking if the sprite is destroyed and removing it if so
		- Running update_move
		- Checking again if the sprite is destroyed and removing it
		- Updating the SpriteGlobalsManager to ensure the validity of the aliases
		- Iterating over all layers and sprites and running update_draw for each Sprite
		"""
		for k in self._sprites.keys():
			x = self._sprites.get(k)
			keep = []
			for sprite in x:
				if sprite._destroyed:
					continue
				sprite.update_move()

				if not sprite._destroyed:
					keep.append(sprite)

			self._sprites[k] = keep

		self.game.spriteglobals.update()

		for x in self._sprites.values():
			for sprite in sorted(x, key=lambda spr: spr.z):
				sprite.update_draw()


class SpriteGlobalsManager(GameModule):
	"""Module for managing aliases to specific Sprites

	Deletes the alias if the Sprite's _destroyed property is True
	"""

	IDMARKER = "spriteglobals"

	def create(self):
		"""Creates a blank object that can have properties added"""
		del self.game

	def update(self):
		"""Check for destroyed sprites and remove their aliases"""

		delete = []
		for k, v in self.__dict__.items():
			if v.is_destroyed():
				delete.append(k)
		for d in delete:
			del self.__dict__[d]


class StallingSpriteManager(SpritesManager):
	"""CURRENTLY BROKEN

	SpritesManager that can stall sprites' update_move method but not their update_draw method

	Can be used for visual effect
	"""

	def create(self, *layer_names):
		"""Create with the same properties as SpritesManager"""
		super().create(*layer_names)

		self._stall_frames = 0
		self._frozen = False

	def stall(self, frames: int):
		"""Stall for n frames"""
		self._stall_frames = frames

	def freeze(self, f: bool = True):
		"""Freeze the StallingSpriteManager's stall_frames decrease"""
		self._frozen = f

	def update(self):
		"""CURRENTLY BROKEN Only update sprites if not currently stalling"""
		if self._stall_frames == 0:
			self._update_move()

		elif not self._frozen:
			self._stall_frames -= 1

		self._update_draw()
