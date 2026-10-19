"""Shared typography, spacing, and keyboard prompts for the 640 x 360 UI."""
import pygame

WIDTH, HEIGHT = 640, 360
INK = (15, 23, 34)
PAPER = (235, 233, 220)
MUTED = (168, 183, 190)
GOLD = (250, 205, 127)
MINT = (133, 218, 192)
BORDER = (53, 72, 86)
_fonts = {}


def font(size):
    if size not in _fonts:
        _fonts[size] = pygame.font.Font(None, size)
    return _fonts[size]


def label(canvas, text, x, y, size=20, color=PAPER, center=False):
    surface = font(size).render(text, True, color)
    rect = surface.get_rect(midtop=(x, y)) if center else surface.get_rect(topleft=(x, y))
    canvas.blit(surface, rect)
    return rect


def lines(text, width, size=20):
    result = []
    for paragraph in text.split("\n"):
        line = ""
        for word in paragraph.split():
            candidate = f"{line} {word}".strip()
            if font(size).size(candidate)[0] > width and line:
                result.append(line)
                line = word
            else:
                line = candidate
        result.append(line)
    return result


def paragraph(canvas, text, x, y, width, size=20, color=PAPER, leading=None):
    for line in lines(text, width, size):
        label(canvas, line, x, y, size, color)
        y += leading or size + 5
    return y


def shade(canvas, alpha=185):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((*INK, alpha))
    canvas.blit(overlay, (0, 0))


def key_width(key, size=17):
    return max(20, font(size).size(key)[0] + 14)


def keycap(canvas, key, x, y, size=17, color=MUTED, filled=False):
    rect = pygame.Rect(x, y, key_width(key, size), 22)
    pygame.draw.rect(canvas, color if filled else (25, 37, 50), rect, border_radius=4)
    if not filled:
        pygame.draw.rect(canvas, BORDER, rect, 1, border_radius=4)
    surface = font(size).render(key, True, INK if filled else color)
    canvas.blit(surface, surface.get_rect(center=rect.center))
    return rect


def action_width(key, text, size=18):
    return key_width(key) + 9 + font(size).size(text)[0]


def action(canvas, key, text, x, y, size=18, color=PAPER, active=False):
    cap = keycap(canvas, key, x, y, color=MINT if active else MUTED, filled=active)
    label(canvas, text, cap.right + 9, y + (22 - font(size).get_height()) // 2, size, color)
    return pygame.Rect(x, y, action_width(key, text, size), 22)


def actions_row(canvas, items, y, center=320, gap=28):
    widths = [action_width(key, text) for key, text in items]
    x = center - (sum(widths) + gap * (len(items) - 1)) // 2
    rects = []
    for (key, text), width in zip(items, widths):
        rects.append(action(canvas, key, text, x, y))
        x += width + gap
    return rects


def card(canvas, title, eyebrow=""):
    shade(canvas, 190)
    pygame.draw.rect(canvas, INK, (40, 34, 560, 292), border_radius=12)
    pygame.draw.rect(canvas, BORDER, (40, 34, 560, 292), 1, border_radius=12)
    if eyebrow:
        label(canvas, eyebrow, 64, 50, 17, MINT)
        label(canvas, title, 64, 74, 29, PAPER)
    else:
        label(canvas, title, 64, 61, 29, PAPER)


def panel_layout(body, note=""):
    """Return text bounds so content can be checked against the action footer."""
    body_lines = lines(body, 512, 21)
    body_bottom = 108 + len(body_lines) * 26
    note_y = body_bottom + 14
    note_bottom = note_y + len(lines(note, 512, 18)) * 23 if note else body_bottom
    return body_bottom, note_y, note_bottom


def panel(canvas, title, body, actions=(("Enter", "Continue"),), note="", eyebrow=""):
    card(canvas, title, eyebrow)
    paragraph(canvas, body, 64, 108, 512, 21, leading=26)
    _, note_y, _ = panel_layout(body, note)
    if note:
        paragraph(canvas, note, 64, note_y, 512, 18, MUTED, leading=23)
    pygame.draw.line(canvas, BORDER, (64, 278), (576, 278))
    actions_row(canvas, actions, 291)


def prompt(canvas, key, text, center, top):
    width = action_width(key, text) + 24
    x = max(8, min(WIDTH - width - 8, center - width // 2))
    rect = pygame.Rect(x, top, width, 34)
    pygame.draw.rect(canvas, INK, rect, border_radius=6)
    pygame.draw.rect(canvas, BORDER, rect, 1, border_radius=6)
    action(canvas, key, text, x + 12, top + 6, color=GOLD)
    return rect
