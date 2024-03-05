class Sprite():
	_destroyed = False

	def update_move(self):
		pass

	def update_draw(self):
		pass

	def destroy(self):
		self._destroyed = True

	def is_destroyed(self):
		return self._destroyed


class SpriteGroup(Sprite):

	def __init__(self):
		self.sprites = []

	def update_move(self):
		keep = []
		for sprite in self.sprites:
			if sprite._destroyed:
				continue
			sprite.update_move()

			if not sprite._destroyed:
				keep.append(sprite)

		self.sprites = keep

	def update_draw(self):
		for sprite in self.sprites:
			sprite.update_draw()
