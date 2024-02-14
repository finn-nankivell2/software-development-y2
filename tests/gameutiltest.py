__all__ = ["traverse_surface", "transmute_surface_palette"]


def traverse_surface(surface):
	w, h = surface.get_size()

	for y in range(h):
		for x in range(w):
			yield (x, y)


def transmute_surface_palette(surface, palette_map):
	surface.lock()
	for pos in traverse_surface(surface):
		c = surface.get_at(pos)
		try:
			newc = next(nc for k, nc in palette_map if k == c)
			surface.set_at(pos, newc)
		except StopIteration:
			pass
	surface.unlock()
	return surface
