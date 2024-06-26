from pygame import Vector2, FRect

# Constants used multiple times across the game
VZERO = Vector2(0, 0)  # Should not mutate
CARD_RECT = FRect(0, 860, 150, 220)
BUILDING_RECT = FRect(100, 100, 400, 250)
HAND_SIZE = 16
TOOLTIP_HOVER_TIME = 40
POLLUTION_UNPLAYED_INCR = 0.1
MAX_INVESMENTS = 10
SERVER_ADDRESS = "http://localhost:5000"


__all__ = ["VZERO", "CARD_RECT", "HAND_SIZE"]
