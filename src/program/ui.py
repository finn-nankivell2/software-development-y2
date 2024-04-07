from prelude import *
import fonts

Onclick = Optional[Callable]


class AbstractButton(Sprite):

	def __init__(self, rect: FRect, onclick: Onclick = None):
		self.rect = rect
		self.onclick = onclick

	def set_onclick(self, onclick: Optional[Callable]):
		self.onclick = onclick
		return self

	def set_pos(self, pos: Vector2):
		self.rect.topleft = pos  # type: ignore
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


class SurfaceButton(AbstractButton):
	LAYER = "UI"

	def __init__(self, rect: FRect, texture: Surface, onclick: Onclick = None):
		super().__init__(rect, onclick)
		self._texture = texture

	@classmethod
	def from_surface(cls, surf: Surface):
		return cls(FRect(surf.get_rect()), surf)

	def update_draw(self):
		game.windowsystem.screen.blit(self._texture, self.rect)


class NamedButton(AbstractButton):
	LAYER = "UI"

	def __init__(self, rect: FRect, text: str, colour: Color = palette.BLACK, onclick: Onclick = None):
		super().__init__(rect, onclick)
		self.c = colour
		self._text = text
		self._font = fonts.families.roboto.size(self.rect.height / 4)
		self._rendered = self._font.render(self._text, True, palette.TEXT)

	def update_draw(self):
		pygame.draw.rect(game.windowsystem.screen, self.c, self.rect, border_radius=5)
		pygame.draw.rect(game.windowsystem.screen, palette.GREY, self.rect.inflate(-10, -10), width=2, border_radius=5)
		game.windowsystem.screen.blit(self._rendered, self.rect.center - Vector2(self._rendered.get_size())/2)



# class ProgressBar(Sprite):

# 	def __init__(self, rect: FRect,
