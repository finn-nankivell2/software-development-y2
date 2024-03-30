from prelude import *
from pygame.font import Font
import fonts


class Tooltip(Sprite):
	LAYER = "UI"
	TOOLTIP_WIDTH = 180
	TITLE_MARGIN = 20
	PADDING = 15

	def __init__(self, title: str, text: str, target: FRect, hover_time: int = 120, titlefont: Font = fonts.NONE_FONT, bodyfont: Font = fonts.NONE_FONT):
		self.title = title
		self.text = text
		self.target = target

		titlerender = titlefont.render(title, True, palette.TEXT, None, Tooltip.TOOLTIP_WIDTH)
		textrender = bodyfont.render(text, True, palette.TEXT, None, Tooltip.TOOLTIP_WIDTH)

		body_start_at = titlerender.get_height() + Tooltip.PADDING + Tooltip.TITLE_MARGIN

		self.rect = FRect(
			0,  # Default position
			0,
			Tooltip.TOOLTIP_WIDTH + Tooltip.PADDING * 2,
			textrender.get_height() + body_start_at + Tooltip.PADDING
		)

		self._surface = Surface(self.rect.size)
		self._surface.fill(palette.TOOLTIP)

		self._surface.blit(titlerender, Vector2(Tooltip.PADDING, Tooltip.PADDING))
		self._surface.blit(textrender, Vector2(Tooltip.PADDING, body_start_at))

		pygame.draw.rect(
			self._surface, palette.GREY, self.rect.inflate(-Tooltip.PADDING // 2, -Tooltip.PADDING // 2), width=1
		)

	def update_move(self):
		pass

	def update_draw(self):
		game.windowsystem.screen.blit(self._surface, self.rect.topleft)
