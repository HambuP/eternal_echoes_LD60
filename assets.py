"""Load bundled art relative to the game, regardless of the launch directory."""
from functools import lru_cache
from pathlib import Path
import pygame

ROOT = Path(__file__).resolve().parent


@lru_cache(maxsize=None)
def picture(relative):
    return pygame.image.load(str(ROOT / relative)).convert_alpha()
