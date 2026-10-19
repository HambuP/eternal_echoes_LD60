import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')
from collections import defaultdict
import pygame


def setup_display():
    pygame.init()
    pygame.display.set_mode((640, 360))


def keys(*pressed):
    return defaultdict(bool, {key: True for key in pressed})


def press(scene, key):
    scene.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key))
