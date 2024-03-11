from pygame import Vector2


_consts = {"VZERO": Vector2(0, 0)}


for a, b in _consts.items():
	globals()[a] = b


__all__ = list(_consts.keys())
