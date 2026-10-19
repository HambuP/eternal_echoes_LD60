"""Fonts, the robot's boot log, and the button sprites. The only text in the game lives here."""
from functools import lru_cache
import random
import pygame
from assets import picture, ROOT

AMBER = (255, 196, 92)
MINT = (160, 232, 180)
INK = (10, 12, 18)
PAPER = (232, 226, 212)
GLITCH = "#%&?/\\|=+"


FONT_PATH = ROOT / "fonts" / "DejaVuSansMono.ttf"     # bundled, so every machine renders the same


@lru_cache(maxsize=None)
def font(size):
    if FONT_PATH.exists():
        return pygame.font.Font(str(FONT_PATH), size)
    return pygame.font.Font(None, size + 4)


@lru_cache(maxsize=4096)
def render(text, size, color):
    """Rendered text is cached: the same line costs nothing on the next frame."""
    return font(size).render(text, True, color)


def glitched(line, frame):
    """`~` in a line renders as a different symbol every few frames."""
    if "~" not in line:
        return line
    rng = random.Random(frame // 4)
    return "".join(rng.choice(GLITCH) if c == "~" else c for c in line)


# Text stays sharp by skipping the pixel-art canvas: when SCALE > 1, label() renders at
# full window resolution and queues the blit; main.py draws the queue onto the window
# after scaling the canvas. FADE is how dark the current scene fade is (0-255).
SCALE = 1
QUEUE = []
FADE = 0


def label(canvas, text, x, y, size=12, color=PAPER, center=False):
    """Draw text at canvas coordinates (sharp, via the queue, when the game is scaled up)."""
    k = SCALE
    img = render(text, size * k, tuple(color))
    rect = img.get_rect()
    if center:
        rect.center = (x * k, y * k)
    else:
        rect.topleft = (x * k, y * k)
    if k > 1:
        QUEUE.append((img, rect))
    else:
        canvas.blit(img, rect)
    return pygame.Rect(rect.x // k, rect.y // k, rect.w // k, rect.h // k)


def flush(screen):
    """Draw the queued text onto the window, then the scene fade over everything."""
    for img, rect in QUEUE:
        screen.blit(img, rect)
    QUEUE.clear()
    if FADE:
        veil = pygame.Surface(screen.get_size())
        veil.set_alpha(FADE)
        screen.blit(veil, (0, 0))
    if SCALE == 1 and FADE:
        pass  # plain-text mode: the scene already faded the canvas itself


class BootLog:
    """Lines of robot self-diagnostics, typed out in the corner, then gone."""
    CHARS_PER_FRAME = 0.6
    LINGER = 150

    def __init__(self):
        self.lines = []
        self.typed = 0.0
        self.linger = 0
        self.frame = 0

    def show(self, lines):
        self.lines = list(lines)
        self.typed = 0.0
        self.linger = self.LINGER

    @property
    def active(self):
        return bool(self.lines)

    def update(self):
        self.frame += 1
        if not self.lines:
            return
        total = sum(len(l) for l in self.lines)
        if self.typed < total:
            self.typed = min(total, self.typed + self.CHARS_PER_FRAME)
        else:
            self.linger -= 1
            if self.linger <= 0:
                self.lines = []

    def draw(self, canvas):
        if not self.lines:
            return
        size = 10
        f = font(size)
        remaining = int(self.typed)
        shown = []
        for line in self.lines:
            take = min(len(line), remaining)
            remaining -= take
            shown.append(line[:take])
            if remaining <= 0:
                break
        width = max(f.size(l)[0] for l in shown) + 24
        height = len(shown) * (size + 4) + 10
        panel = pygame.Surface((width, height), pygame.SRCALPHA)
        panel.fill((*INK, 190))
        canvas.blit(panel, (8, 8))
        for i, line in enumerate(shown):
            cursor = "_" if (i == len(shown) - 1 and self.frame // 15 % 2 == 0) else ""
            label(canvas, glitched(line, self.frame) + cursor, 16, 13 + i * (size + 4), size, AMBER)


BUTTONS = {
    "start": pygame.Rect(26, 20, 133, 55),
    "menu": pygame.Rect(202, 20, 91, 26),
    "controls": pygame.Rect(202, 48, 91, 24),
}


def button(name):
    return picture("background/buttons.png").subsurface(BUTTONS[name])


def draw_button(canvas, name, center, hot=False):
    img = button(name)
    if hot:
        img = pygame.transform.scale(img, (int(img.get_width() * 1.08), int(img.get_height() * 1.08)))
    rect = img.get_rect(center=center)
    canvas.blit(img, rect)
    return rect
