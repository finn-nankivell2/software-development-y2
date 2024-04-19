import json
from types import SimpleNamespace
from typing import Dict, Any, Optional
from dataclasses import dataclass

import pygame.font
from pygame.font import Font

# Init fonts
pygame.font.init()

# Default font
NONE_FONT = pygame.font.Font(None, 28)


# Class representing a font family and all of the different sizes availible
@dataclass
class FontFamily:
	path: str
	default: Optional[Font]
	sizes: Dict[int, Font]

	@classmethod
	def fromjson(cls, jdict: Dict[str, Any]):
		path = jdict["path"]
		sizes = {size: Font(path, size) for size in jdict["sizes"]}

		return FontFamily(path=path, default=next(sizes.values().__iter__(), None), sizes=sizes)

	def size(self, x: int) -> Font:
		if not self.sizes.get(x):
			self.sizes[x] = Font(self.path, x)

		return self.sizes[x]


# Load fonts defined in data/assets.json
with open("data/assets.json") as file:
	jdict = json.load(file)
	fonts = jdict["fonts"]

	global families
	families = SimpleNamespace(**{k: FontFamily.fromjson(j) for k, j in fonts.items()})
