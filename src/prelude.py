from consts import VZERO
import consts

import palette

import pygame
from pygame import Vector2, Rect, FRect, Color, Surface
vec = Vector2

from gamesystem.common.sprite import Sprite, SpriteGroup
from gamesystem import game

from typing import Optional, Dict, List, Tuple, Union, Any, Callable, Iterator

import math
import logging
import random
import itertools
import functools

from dataclasses import dataclass
from types import SimpleNamespace

from pprint import pprint, pformat
