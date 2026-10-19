"""Title, controls, room select, play, pause, cutscenes, end.
Nothing on screen during play but the house, the robot, and the robot's boot log."""
import math
import random
import pygame
import levels
import player
import progress
import text
from assets import picture
from camera import Camera
from sound import soundscape
from text import BootLog, label, draw_button, glitched, AMBER, PAPER

VIEW_W, VIEW_H = 426, 240            # what the player sees of the 640x360 room
ROOM_W, ROOM_H = levels.ROOM_W, levels.ROOM_H
FADE_FRAMES = 28
LIGHT_RADIUS = {levels.FULL: None, levels.DIM: 115, levels.CRITICAL: 54}
CAMERA_LERP = (0.08, 0.07, 0.06, 0.05, 0.045, 0.04)     # by wear: the camera gets sluggish too
STATIC = (0, 10, 18, 28, 40, 52)                        # by wear: noise on the robot's view


def to_canvas(pos, canvas, screen):
    """Mouse position on the window -> position on the canvas."""
    return (pos[0] * canvas.get_width() / screen.get_width(),
            pos[1] * canvas.get_height() / screen.get_height())


def full_picture(canvas, path):
    canvas.blit(pygame.transform.smoothscale(picture(path), canvas.get_size()), (0, 0))


class Scene:
    def __init__(self):
        self.next_scene = None
        self.fade_in = FADE_FRAMES
        self.fade_out = 0
        self.after_fade = None
        self.frames = 0

    def leave(self, scene):
        """Fade to black, then switch."""
        if self.after_fade is None:
            self.after_fade = scene
            self.fade_out = 1

    def handle_event(self, event):
        pass

    def update(self):
        self.frames += 1
        if self.fade_in:
            self.fade_in -= 1
        if self.fade_out:
            self.fade_out += 1
            if self.fade_out > FADE_FRAMES:
                self.next_scene = self.after_fade
        return self.fade_out > 0

    def draw_fade(self, canvas):
        alpha = 0
        if self.fade_in:
            alpha = 255 * self.fade_in / FADE_FRAMES
        if self.fade_out:
            alpha = 255 * min(1, self.fade_out / FADE_FRAMES)
        text.FADE = int(alpha)
        if alpha and text.SCALE == 1:
            veil = pygame.Surface(canvas.get_size())
            veil.set_alpha(int(alpha))
            canvas.blit(veil, (0, 0))

    def draw(self, canvas):
        pass


class Buttons:
    """Click/hover handling for the sprite buttons."""
    def __init__(self):
        self.rects = {}
        self.hot = None

    def event(self, event):
        """Returns the name of the button clicked, if any."""
        if event.type == pygame.MOUSEMOTION:
            self.hot = next((n for n, r in self.rects.items() if r.collidepoint(event.pos)), None)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            return next((n for n, r in self.rects.items() if r.collidepoint(event.pos)), None)
        return None

    def draw(self, canvas, name, center):
        self.rects[name] = draw_button(canvas, name, center, self.hot == name)


class Title(Scene):
    def __init__(self):
        super().__init__()
        self.buttons = Buttons()

    def handle_event(self, event):
        if self.fade_out:
            return
        clicked = self.buttons.event(event)
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE) or clicked == "start":
            self.leave(RoomSelect())
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_c or clicked == "controls":
            self.leave(Controls(Title))

    def draw(self, canvas):
        full_picture(canvas, "background/main.png")
        self.buttons.draw(canvas, "start", (330, 186))
        self.buttons.draw(canvas, "controls", (330, 222))
        self.draw_fade(canvas)


class Controls(Scene):
    ROWS = (("MOVE", "arrows / A D"), ("JUMP", "up / W / space"), ("", "hold to jump higher"),
            ("SPRINT", "shift, while it lasts"), ("RESTART", "R"), ("PAUSE", "esc"), ("MUSIC", "M"))

    def __init__(self, back):
        super().__init__()
        self.back = back            # a callable that builds the scene to return to
        self.buttons = Buttons()

    def handle_event(self, event):
        if self.fade_out:
            return
        clicked = self.buttons.event(event)
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN) or clicked == "menu":
            self.leave(self.back())

    def draw(self, canvas):
        full_picture(canvas, "background/menu.png")
        label(canvas, "CONTROLS", 310, 40, 12, AMBER, center=True)
        for i, (key, what) in enumerate(self.ROWS):
            y = 66 + i * 16
            label(canvas, key, 205, y, 9, AMBER)
            label(canvas, what, 268, y, 9, PAPER)
        self.buttons.draw(canvas, "menu", (310, 205))
        self.draw_fade(canvas)


class RoomSelect(Scene):
    # label centers in levels.png (640x360 coordinates)
    LABELS = [(386, 114), (546, 114), (386, 230), (551, 230), (465, 337)]
    THUMB = (112, 63)

    def __init__(self, unlocked=None):
        super().__init__()
        self.unlocked = unlocked or progress.load()
        self.index = min(self.unlocked, 5) - 1
        self.thumbs = [self.thumbnail(i) for i in range(5)]

    def thumbnail(self, i):
        img = pygame.transform.smoothscale(picture(levels.LEVELS[i]["background"]), self.THUMB)
        if i >= self.unlocked:
            grey = img.copy()                       # desaturate by hand: works on pygame and pygame-ce
            for x in range(grey.get_width()):
                for y in range(grey.get_height()):
                    r, g, b, a = grey.get_at((x, y))
                    v = (r * 30 + g * 59 + b * 11) // 100
                    grey.set_at((x, y), (v * 70 // 255, v * 70 // 255, v * 80 // 255, a))
            return grey
        return img

    def scale(self):
        return VIEW_W / 640, VIEW_H / 360

    def slot(self, i):
        """Canvas rectangle covering thumbnail + label for room i."""
        sx, sy = self.scale()
        cx, cy = self.LABELS[i]
        rect = pygame.Rect(0, 0, int(120 * sx), int(88 * sy))
        rect.center = (int(cx * sx), int((cy - 28) * sy))
        return rect

    def handle_event(self, event):
        if self.fade_out:
            return
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RIGHT, pygame.K_d, pygame.K_DOWN, pygame.K_s):
                self.index = (self.index + 1) % 5
            elif event.key in (pygame.K_LEFT, pygame.K_a, pygame.K_UP, pygame.K_w):
                self.index = (self.index - 1) % 5
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.choose(self.index)
            elif event.key == pygame.K_ESCAPE:
                self.leave(Title())
        elif event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
            for i in range(5):
                if self.slot(i).collidepoint(event.pos):
                    self.index = i
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        self.choose(i)

    def choose(self, i):
        if i < self.unlocked:
            self.leave(Intro() if i == 0 else Play(i))

    def draw(self, canvas):
        full_picture(canvas, "background/menu.png")
        full_picture(canvas, "background/levels.png")
        sx, sy = self.scale()
        for i in range(5):
            cx, cy = self.LABELS[i]
            thumb = self.thumbs[i]
            size = (int(self.THUMB[0] * sx), int(self.THUMB[1] * sy))
            rect = pygame.Rect(0, 0, *size)
            rect.midbottom = (int(cx * sx), int((cy - 14) * sy))
            canvas.blit(pygame.transform.smoothscale(thumb, size), rect)
            if i >= self.unlocked:
                shade = pygame.Surface(rect.size, pygame.SRCALPHA)
                shade.fill((20, 20, 30, 110))
                canvas.blit(shade, rect)
            if i == self.index:
                pulse = 150 + int(60 * math.sin(self.frames / 10))
                pygame.draw.rect(canvas, (255, 196 + pulse // 6, 92) if i < self.unlocked else (120, 120, 130),
                                 rect.inflate(6, 6), 2, border_radius=2)
        if self.index >= self.unlocked:
            label(canvas, "LOCKED", VIEW_W // 2 + 60, VIEW_H - 14, 9, PAPER, center=True)
        self.draw_fade(canvas)


class Dust:
    def __init__(self, x, y, count, spread):
        self.bits = [[x + random.uniform(-spread, spread), y, random.uniform(-0.6, 0.6),
                      random.uniform(-0.8, -0.2), random.randint(14, 26)] for _ in range(count)]

    def update(self):
        for b in self.bits:
            b[0] += b[2]
            b[1] += b[3]
            b[3] += 0.03
            b[4] -= 1
        self.bits = [b for b in self.bits if b[4] > 0]

    def draw(self, surface):
        for x, y, _, _, life in self.bits:
            pygame.draw.circle(surface, (120, 112, 100), (int(x), int(y)), 1 + life // 9)


def ghost_of(img, alpha):
    """A translucent copy that keeps per-pixel edges clean (set_alpha darkens the fringe)."""
    out = img.copy()
    out.fill((255, 255, 255, alpha), special_flags=pygame.BLEND_RGBA_MULT)
    return out


class Play(Scene):
    def __init__(self, levelnum=0):
        super().__init__()
        self.levelnum = levelnum
        self.data = levels.LEVELS[levelnum]
        self.background = picture(self.data["background"])
        self.foreground = []
        for path, pos in self.data["foreground"]:
            img = picture(path)
            self.foreground.append((img, ghost_of(img, 165), pygame.Rect(pos, img.get_size())))
        self.star_img = pygame.transform.scale(picture("background/star.png"), (24, 24))
        self.star = pygame.Rect(*self.data["goalpos"], 32, 32)
        self.exit_zone = levels.exit_zone(levelnum)
        self.abilities = dict(self.data["abilities"])
        self.wear = levelnum
        self.robot = player.Player(self.data["start_pos"], self.data["car_size"], levelnum,
                                   self.abilities["jump"], self.abilities["run"], wear=self.wear)
        self.edge_left = pygame.Rect(-50, -1000, 50, 3000)
        self.edge_right = pygame.Rect(ROOM_W, -1000, 50, 3000)
        self.base_walls = list(self.data["boxes"].walls)
        self.platforms = list(self.data["boxes"].platforms)
        self.room = pygame.Surface((ROOM_W, ROOM_H))
        self.darkness = pygame.Surface((ROOM_W, ROOM_H), pygame.SRCALPHA)
        self.static = pygame.Surface((VIEW_W, VIEW_H))
        self.camera = Camera((VIEW_W, VIEW_H), (ROOM_W, ROOM_H))
        self.camera.snap(self.robot.rect, True)
        self.log = BootLog()
        self.log.show(self.data["enter"])
        self.collected = False
        self.collect_timer = 0          # counts down through the pickup sequence
        self.flash = self.glitch = self.squash = 0
        self.dust = []
        self.debug = False
        self.flicker = 0.0
        self.hint = self.data.get("hint")
        self.hint_rect = pygame.Rect(self.hint[0]) if self.hint else None
        self.hint_shown = False
        self.stuck = 0

    @property
    def walls(self):
        """The screen edges are walls until the star opens one of them."""
        walls = list(self.base_walls)
        if not (self.collected and self.data["exit"] == "left"):
            walls.append(self.edge_left)
        if not (self.collected and self.data["exit"] == "right"):
            walls.append(self.edge_right)
        return walls

    # ---- game flow -------------------------------------------------------
    def pickup(self):
        soundscape.silence_robot()
        self.robot.start_collect()
        self.collect_timer = 70 if self.data["loses"] else 45
        self.flash = 24
        self.camera.hold = 36
        self.collected = True

    def apply_loss(self):
        lost = self.data["loses"]
        if lost == "run":
            self.abilities["run"] = self.robot.can_run = False
        elif lost == "jump":
            self.abilities["jump"] = self.robot.can_jump = False
        elif lost == "light":
            self.abilities["light"] = levels.DIM if self.abilities["light"] == levels.FULL else levels.CRITICAL
        self.wear = self.levelnum + 1
        self.robot.set_wear(self.wear)
        self.log.show(self.data["pickup"])

    def finish_room(self):
        soundscape.silence_robot()
        unlocked = progress.unlock(self.levelnum + 2)
        if self.data["exit"] == "bear":
            self.leave(End(self))
        else:
            self.leave(Cutscene(self.levelnum, lambda: RoomSelect(unlocked)))

    def restart(self):
        self.leave(Play(self.levelnum))

    # ---- input / update --------------------------------------------------
    def handle_event(self, event):
        if self.fade_out or event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_ESCAPE:
            self.next_scene = Pause(self)
        elif event.key == pygame.K_r:
            self.restart()
        elif event.key == pygame.K_F1:
            self.debug = not self.debug
        elif not self.collect_timer:
            self.robot.handle_event(event)

    def update(self, keys=None):
        if super().update():
            return
        self.log.update()
        self.flash = max(0, self.flash - 1)
        self.glitch = max(0, self.glitch - 1)
        self.squash = max(0, self.squash - 1)
        for d in self.dust:
            d.update()
        self.dust = [d for d in self.dust if d.bits]
        if self.frames % 3 == 0:
            self.flicker = random.uniform(-6, 6)
        self.camera.lerp = CAMERA_LERP[self.wear]
        if self.collect_timer:
            self.collect_timer -= 1
            if self.collect_timer == 40 and self.data["loses"]:
                self.glitch = 22
                self.camera.kick(10)
                self.apply_loss()
            elif self.collect_timer == 40:
                self.wear = self.levelnum + 1
                self.robot.set_wear(self.wear)
                self.log.show(self.data["pickup"])
            if not self.collect_timer:
                self.robot.collecting = False
            self.camera.update(self.robot.rect, self.robot.right)
            return
        if keys is None:
            keys = pygame.key.get_pressed()
        previous_x = self.robot.rect.x
        previous_dy = self.robot.dy
        was_grounded, was_right = self.robot.onground, self.robot.right
        self.robot.update(keys, self.walls, self.platforms)
        moving = self.robot.rect.x != previous_x
        landed = not was_grounded and self.robot.onground and previous_dy < -1.5
        if landed:
            self.squash = 8
            self.dust.append(Dust(self.robot.rect.centerx, self.robot.rect.bottom, 4, 10))
            if previous_dy < -7.5:
                self.camera.kick(6)
        if self.robot.jumped:
            self.dust.append(Dust(self.robot.rect.centerx, self.robot.rect.bottom, 3, 6))
        soundscape.update_robot(self.robot, moving=moving, jumped=self.robot.jumped, landed=landed,
                                turned=moving and self.robot.right != was_right)
        if self.robot.rect.top > ROOM_H:
            self.robot.teleport(self.data["start_pos"])
        if self.levelnum == 2 and any(self.robot.rect.colliderect(h) for h in levels.SINK_HOLES) and self.robot.onground:
            self.stuck += 1            # fell into the sink: nothing to climb, the log suggests a restart
            if self.stuck == 60:
                self.log.show(["SINK. NO EXIT.", "R: REBOOT ROOM."])
        else:
            self.stuck = 0
        if self.hint_rect and not self.hint_shown and not self.log.active and self.robot.rect.colliderect(self.hint_rect):
            self.hint_shown = True
            self.log.show([self.hint[1]])
        if not self.collected and self.robot.rect.colliderect(self.star):
            self.pickup()
        elif self.collected and self.robot.rect.colliderect(self.exit_zone):
            self.finish_room()
        self.camera.update(self.robot.rect, self.robot.right)

    # ---- drawing ---------------------------------------------------------
    def draw_star(self, surface, glow_only=False):
        bob = int(2 * math.sin(self.frames / 12))
        cx, cy = self.star.left + 12, self.star.top + 12 + bob
        glow = pygame.Surface((80, 80), pygame.SRCALPHA)
        for r, a in ((36, 18), (24, 30), (14, 55)):
            pygame.draw.circle(glow, (255, 220, 120, a + int(6 * math.sin(self.frames / 9))), (40, 40), r)
        surface.blit(glow, (cx - 40, cy - 40))
        if not glow_only:
            surface.blit(self.star_img, (cx - 12, cy - 12))

    def draw_robot(self, surface):
        img = self.robot.current if self.robot.right else pygame.transform.flip(self.robot.current, True, False)
        rect = self.robot.rect_draw
        if self.squash:
            k = self.squash / 8
            img = pygame.transform.scale(img, (int(64 * (1 + 0.12 * k)), int(64 * (1 - 0.14 * k))))
            rect = img.get_rect(midbottom=rect.midbottom)
        surface.blit(img, rect)

    def draw_darkness(self, surface):
        radius = LIGHT_RADIUS[self.abilities["light"]]
        if radius is None:
            return
        if self.abilities["light"] == levels.CRITICAL:
            radius += self.flicker
        self.darkness.fill((4, 8, 18, 232))
        center = self.robot.rect.center
        for extra, alpha in ((30, 190), (20, 130), (10, 60), (0, 0)):
            pygame.draw.circle(self.darkness, (0, 0, 0, alpha), center, int(radius + extra))
        surface.blit(self.darkness, (0, 0))

    def draw_exit_light(self, surface):
        """Once the star is taken, light from the next room spills in at the open edge."""
        if not self.collected or self.data["exit"] not in ("left", "right"):
            return
        width = 26
        pulse = 60 + int(25 * math.sin(self.frames / 16))
        glow = pygame.Surface((width, ROOM_H), pygame.SRCALPHA)
        for i in range(width):
            k = (width - i) / width if self.data["exit"] == "left" else (i + 1) / width
            pygame.draw.line(glow, (255, 236, 190, int(pulse * k * k)), (i, 0), (i, ROOM_H))
        surface.blit(glow, (0 if self.data["exit"] == "left" else ROOM_W - width, 0))

    def draw_room(self):
        room = self.room
        room.blit(self.background, (0, 0))
        if not self.collected:
            self.draw_star(room)
        for d in self.dust:
            d.draw(room)
        self.draw_robot(room)
        for img, ghost, rect in self.foreground:
            room.blit(ghost if rect.colliderect(self.robot.rect_draw) else img, rect)
        self.draw_darkness(room)
        self.draw_exit_light(room)
        if LIGHT_RADIUS[self.abilities["light"]] is not None and not self.collected:
            self.draw_star(room, glow_only=True)   # the star glows through the dark
        if self.debug:
            for rect in self.walls:
                pygame.draw.rect(room, (255, 80, 90), rect, 1)
            for rect in self.platforms:
                pygame.draw.rect(room, (120, 230, 160), rect, 1)
            pygame.draw.rect(room, AMBER, self.robot.rect, 1)
            pygame.draw.rect(room, (255, 255, 0), self.star, 1)

    def draw_static(self, canvas):
        alpha = STATIC[self.wear]
        if not alpha:
            return
        self.static.fill((0, 0, 0))
        for _ in range(140 + 60 * self.wear):
            x, y = random.randrange(VIEW_W), random.randrange(VIEW_H)
            v = random.randint(90, 200)
            self.static.fill((v, v, v), (x, y, 2, 1))
        y = (self.frames * 3) % (VIEW_H + 40) - 40       # a slow rolling scanline band
        pygame.draw.rect(self.static, (40, 40, 40), (0, y, VIEW_W, 14))
        self.static.set_alpha(alpha)
        canvas.blit(self.static, (0, 0))

    def draw(self, canvas, with_log=True):
        self.draw_room()
        canvas.blit(self.room, (0, 0), area=self.camera.view())
        self.draw_static(canvas)
        if self.glitch:
            for _ in range(6):
                y = random.randint(0, VIEW_H - 8)
                h = random.randint(2, 8)
                strip = canvas.subsurface((0, y, VIEW_W, h)).copy()
                canvas.blit(strip, (random.randint(-14, 14), y))
            if self.glitch % 4 < 2:
                tint = pygame.Surface(canvas.get_size())
                tint.fill((60, 20, 20))
                canvas.blit(tint, (0, 0), special_flags=pygame.BLEND_ADD)
        if self.flash:
            veil = pygame.Surface(canvas.get_size())
            veil.fill((255, 240, 200))
            veil.set_alpha(int(150 * self.flash / 24))
            canvas.blit(veil, (0, 0))
        if with_log:
            self.log.draw(canvas)
            if self.stuck > 30:
                box = pygame.Surface((92, 16), pygame.SRCALPHA)
                box.fill((10, 12, 18, 190))
                canvas.blit(box, (VIEW_W - 100, 8))
                if self.frames // 20 % 2:
                    label(canvas, "R  RESTART", VIEW_W - 54, 16, 9, AMBER, center=True)
        self.draw_fade(canvas)


class Pause(Scene):
    def __init__(self, play):
        super().__init__()
        self.play = play
        self.fade_in = 0
        self.buttons = Buttons()
        soundscape.silence_robot()

    def handle_event(self, event):
        if self.fade_out:
            return
        clicked = self.buttons.event(event)
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
            self.next_scene = self.play
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            self.leave(Play(self.play.levelnum))
        elif clicked == "menu":
            self.leave(Title())
        elif clicked == "controls":
            self.leave(Controls(lambda: Pause(self.play)))

    def draw(self, canvas):
        full_picture(canvas, "background/menu.png")
        label(canvas, "PAUSED", 300, 48, 12, AMBER, center=True)
        self.buttons.draw(canvas, "menu", (300, 92))
        self.buttons.draw(canvas, "controls", (300, 126))
        label(canvas, "ESC  continue      R  restart room", 300, 170, 9, PAPER, center=True)
        self.draw_fade(canvas)


class LogScreen(Scene):
    """A picture (or black) with the robot's log typing a few lines underneath. The story lives here."""
    def __init__(self, path, lines, then, hold=200, color=AMBER):
        super().__init__()
        self.image = picture(path) if path else None
        self.lines = lines
        self.then = then
        self.hold = hold
        self.color = color
        self.typed = 0.0

    @property
    def total(self):
        return sum(len(l) for l in self.lines)

    def handle_event(self, event):
        if self.frames > 30 and event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
            if self.typed < self.total:
                self.typed = self.total          # first press: show everything
            else:
                self.leave(self.then())          # second press: move on

    def update(self):
        if super().update():
            return
        if self.frames > 10:
            self.typed = min(self.total, self.typed + 0.7)
        if self.typed >= self.total:
            self.hold -= 1
            if self.hold <= 0:
                self.leave(self.then())

    def draw(self, canvas):
        canvas.fill((0, 0, 0))
        if self.image:
            zoom = 1.0 + 0.05 * min(1, self.frames / 600)
            size = (int(VIEW_W * zoom), int(VIEW_H * zoom))
            img = pygame.transform.smoothscale(self.image, size)
            canvas.blit(img, img.get_rect(center=(VIEW_W // 2, VIEW_H // 2)))
        n = len(self.lines)
        panel_h = n * 14 + 14
        top = VIEW_H - panel_h - 8 if self.image else (VIEW_H - panel_h) // 2
        band = pygame.Surface((VIEW_W - 16, panel_h), pygame.SRCALPHA)
        band.fill((10, 12, 18, 200 if self.image else 0))
        canvas.blit(band, (8, top))
        remaining = int(self.typed)
        for i, line in enumerate(self.lines):
            take = min(len(line), remaining)
            remaining -= take
            if take == 0 and i > 0:
                break
            cursor = "_" if (take < len(line) or remaining <= 0) and self.frames // 15 % 2 == 0 else ""
            label(canvas, glitched(line[:take], self.frames) + cursor, 18, top + 8 + i * 14, 9,
                  self.color if i else PAPER)
            if remaining <= 0:
                break
        if self.frames // 40 % 2 == 0:
            label(canvas, "any key", VIEW_W - 36, VIEW_H - 10, 7, (120, 120, 130), center=True)
        self.draw_fade(canvas)


def Intro():
    return LogScreen(None, levels.INTRO, lambda: Play(0), hold=120)


def Cutscene(levelnum, then):
    data = levels.LEVELS[levelnum]
    lines = levels.MEMORIES[levelnum]
    corrupted = data["cutscene"] is None
    return LogScreen(data["cutscene"], lines, then, hold=220, color=(190, 70, 70) if corrupted else AMBER)


class End(Scene):
    """Reach the bear: the robot's last lines in the room, then the bear, then Miri, then power-down."""
    def __init__(self, play):
        super().__init__()
        self.play = play
        play.fade_out, play.after_fade = 0, None
        self.log = BootLog()
        self.log.LINGER = 10 ** 6
        self.log.show(levels.ENDING)

    def handle_event(self, event):
        if self.frames > 60 and event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
            self.after()

    def after(self):
        self.leave(LogScreen("background/cutscene_4.png", levels.ENDING_BEAR,
                   lambda: LogScreen("background/cutscene_5.png", levels.ENDING_MIRI,
                                     lambda: PowerDown(), hold=260, color=(190, 70, 70)),
                   hold=200))

    def update(self):
        if super().update():
            return
        self.log.update()
        if self.frames == 260:
            self.after()

    def draw(self, canvas):
        self.play.draw(canvas, with_log=False)
        self.log.draw(canvas)
        self.draw_fade(canvas)


class PowerDown(Scene):
    def __init__(self):
        super().__init__()
        self.fade_in = 0
        self.miri = picture("background/cutscene_5.png")

    def handle_event(self, event):
        if self.frames > 200 and event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
            self.leave(Title())

    def update(self):
        if super().update():
            return
        if self.frames == 420:
            self.leave(Title())

    def draw(self, canvas):
        canvas.fill((0, 0, 0))
        f = self.frames
        k = min(1, f / 45)                                   # the picture collapses to a line, like an old TV
        h = max(1, int(VIEW_H * (1 - k)))
        if h > 2:
            img = pygame.transform.smoothscale(self.miri, (VIEW_W, h))
            img.set_alpha(int(255 * (1 - k * 0.6)))
            canvas.blit(img, (0, (VIEW_H - h) // 2))
        elif f < 70:
            pygame.draw.line(canvas, (220, 220, 230), (0, VIEW_H // 2), (VIEW_W, VIEW_H // 2), 1)
        if f > 110:
            label(canvas, "ECHOES IN THE HOUSE", VIEW_W // 2, VIEW_H // 2 - 8, 12, PAPER, center=True)
        if f > 170:
            label(canvas, "PIP-7 waited 4,312 days. It would have waited more.", VIEW_W // 2, VIEW_H // 2 + 14, 9, AMBER, center=True)
        self.draw_fade(canvas)
