from prelude import *


class AbstractButton(Sprite):
	def __init__(self, rect: FRect, onclick: Optional[Callable] = None):
		self.rect = rect
		self.onclick = onclick

	def set_onclick(self, onclick: Optional[Callable]):
		self.onclick
		return self

	def hovered(self) -> bool:
		return game.input.mouse_within(self.rect)

	def clicked(self, mbtn=0) -> bool:
		return self.hovered() and game.input.mouse_pressed(mbtn)

	def update_move(self):
		if self.clicked():
			self.onclick()

	def update_draw(self):
		pygame.draw.rect(game.windowsystem.screen, palette.ERROR, self.rect)


class Button(AbstractButton):
	LAYER = "UI"

	def __init__(self, rect: FRect, texture: Surface, onclick: Optional[Callable] = None):
		super().__init__(rect, onclick)
		self._texture = texture

	@classmethod
	def from_surface(cls, surf: Surface):
		return cls(FRect(surf.get_rect()), surf)

	def update_draw(self):
		game.windowsystem.screen.blit(self._texture, self.rect)
