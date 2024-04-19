from prelude import *
from pygame.font import Font
import fonts


# Tooltip class that appears when a target rect is hovered
class Tooltip(Sprite):
	LAYER = "UI"
	TOOLTIP_WIDTH = 180
	TITLE_MARGIN = 20
	PADDING = 15

	def __init__(
		self,
		title: str,
		text: str,
		target: FRect,
		hover_time: int = consts.TOOLTIP_HOVER_TIME,
		titlefont: Font = fonts.families.roboto.size(24),
		bodyfont: Font = fonts.families.roboto.size(16),
		parent: Optional[Any] = None  # If parent is set, the Tooltip will destroy when the parent is destroyed
	):
		self.title = title
		self.text = text
		self.target = target
		self.parent = parent

		# Render Tooltip text
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

		self._shown = 0
		self.hover_time = hover_time

		self.invisible = False

	# Count the number of frames until the Tooltip should be shown
	def _update_hover(self):
		if game.input.mouse_within(self.target):
			if game.input.mouse.any():
				self._shown = 0

			if self._shown < self.hover_time:
				self._shown += 1

		else:
			self._shown = 0

	# Is the Tooltip currently visible
	def visible(self):
		return self._shown >= self.hover_time and not self.invisible

	def _out_of_bounds(self):
		return self.rect.clamp(game.windowsystem.rect) != self.rect

	def update_move(self):
		self._update_hover()

		if self.visible():
			mp = game.input.mouse_pos()
			self.rect.topleft = mp

			if self._out_of_bounds():
				self.rect.bottomleft = mp

			if self._out_of_bounds():
				self.rect.topright = mp

			if self._out_of_bounds():
				self.rect.bottomright = mp

		if self.parent and self.parent.is_destroyed():
			self.destroy()

	# Draw if visible
	def update_draw(self):
		if self.visible():
			game.windowsystem.screen.blit(self._surface, self.rect.topleft)
