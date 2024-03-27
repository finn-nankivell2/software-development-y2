from prelude import *
from gameutil import surface_rounded_corners, shadow_from_rect
from consts import CARD_RECT


class Playspace(Sprite):
	LAYER = "PLAYSPACE"
	DRAGABLE_BAR_HEIGHT = 25
	MAX_DRAG_FRAMES = 10

	def __init__(self, rect, surface):
		self.rect = rect
		self.titlebar = self.rect.copy()
		self.titlebar.height = Playspace.DRAGABLE_BAR_HEIGHT
		self._dragged = False
		self._drag_offset = Vector2(0, 0)
		self._dragged_frames = 0
		self._dragged_poe = None

		self.surface = game.textclip.get_or_insert(surface, rect.size)
		self.surface = surface_rounded_corners(self.surface, 5)
		self._shadow = shadow_from_rect(self.surface.get_rect(), border_radius=5)
		self._invalid_shadow = shadow_from_rect(self.surface.get_rect(), Color("#90334E"), border_radius=5)

	# TODO
	def play_card_onto_space(self, card):
		pass

	def is_dragged(self) -> bool:
		return self._dragged

	def _permission_to_drag(self) -> bool:
		return not any(space.is_dragged() for space in game.sprites.get("PLAYSPACE") if space is not self)

	# TODO: Fix this for when camera stuff is happening
	def collidecard(self, card) -> bool:
		return self.rect.colliderect(
			card.rect.inflate(-card.PLAYABLE_OVERLAP, -card.PLAYABLE_OVERLAP)
		) and not self._dragged

	def _invalid_placement(self) -> bool:
		"""Returns True if placement is invalid, playspace will return to initial position before dragging begun"""
		return any(self.collidecard(card) for card in game.sprites.get("CARD")
					) or self.rect.bottom > game.windowsystem.dimensions.y - CARD_RECT.height or any(
						self.rect.colliderect(space.rect) for space in game.sprites.get("PLAYSPACE") if space is not self
					)

	def _drop_drag(self):
		self._dragged = False
		if self._invalid_placement():
			pass
		else:
			self._dragged_poe = None

	def _check_for_drag(self) -> bool:
		return game.input.mouse_pressed(0) and game.input.mouse_within(self.titlebar) and self._permission_to_drag()

	def update_move(self):
		if self._check_for_drag():
			self._dragged = True
			self._drag_offset = game.input.mouse_pos() - self.titlebar.topleft
			self._dragged_poe = self.titlebar.topleft

		if self._dragged:
			self._dragged_frames += 1
			target = game.input.mouse_pos() - self._drag_offset
			self.rect.topleft = target

			if not game.input.mouse_down(0):
				self._drop_drag()

		else:
			if self._dragged_poe is not None:
				mv = (Vector2(self.rect.topleft) - self._dragged_poe) / 10
				self.rect.topleft -= mv
				if mv.magnitude() < 0.1:
					self.rect.topleft = self._dragged_poe
					self._dragged_poe = None

			if self._dragged_frames > 0:
				self._dragged_frames -= 1

		if self._dragged_frames > Playspace.MAX_DRAG_FRAMES:
			self._dragged_frames = Playspace.MAX_DRAG_FRAMES

		self.titlebar.topleft = self.rect.topleft

		# Should be above other playspaces if it is being dragged or was just dragged
		self.z = int(self._dragged or self._dragged_frames)

	def update_draw(self):
		if self._dragged_frames > 0:
			if self._invalid_placement():
				game.windowsystem.screen.blit(self._invalid_shadow, self.rect.topleft)
			else:
				game.windowsystem.screen.blit(self._shadow, self.rect.topleft)

		mo = min(Playspace.MAX_DRAG_FRAMES, self._dragged_frames)
		bpos = self.rect.topleft - Vector2(mo, mo)

		game.windowsystem.screen.blit(self.surface, bpos)
		pygame.draw.rect(game.windowsystem.screen, Color("#ff00ff"), self.titlebar.move(-mo, -mo))
