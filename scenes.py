"""Story, interaction, and compact UI for the five-room delivery."""
import math
import pygame
import levels
import player
from assets import picture
from campaign import Campaign, SaveStore, MODULES, MODULE_NAMES

WIDTH, HEIGHT = 640, 360
INK = (15, 23, 34)
PAPER = (231, 230, 214)
MUTED = (160, 178, 184)
GOLD = (255, 205, 111)
MINT = (125, 229, 192)
_fonts = {}


def font(size):
    if size not in _fonts:
        _fonts[size] = pygame.font.Font(None, size)
    return _fonts[size]


def label(canvas, text, x, y, size=18, color=PAPER, center=False):
    surface = font(size).render(text, True, color)
    canvas.blit(surface, surface.get_rect(midtop=(x, y)) if center else (x, y))


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


def paragraph(canvas, text, x, y, width, size=20, color=PAPER):
    for line in lines(text, width, size):
        label(canvas, line, x, y, size, color)
        y += size + 3
    return y


def shade(canvas, alpha=185):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((*INK, alpha))
    canvas.blit(overlay, (0, 0))


def panel(canvas, title, body, hint="ENTER / E to continue", note=""):
    shade(canvas)
    pygame.draw.rect(canvas, INK, (38, 56, 564, 254), border_radius=12)
    pygame.draw.rect(canvas, (77, 112, 115), (38, 56, 564, 254), 1, border_radius=12)
    label(canvas, title, 60, 76, 29, GOLD)
    bottom = paragraph(canvas, body, 60, 116, 518, 21)
    if note:
        paragraph(canvas, note, 60, bottom + 12, 518, 18, MINT)
    label(canvas, hint, 320, 282, 18, MUTED, center=True)


class Scene:
    def __init__(self):
        self.next_scene = None

    def handle_event(self, event):
        pass

    def update(self):
        pass

    def draw(self, canvas):
        pass


class Menu(Scene):
    def __init__(self, store=None):
        super().__init__()
        self.store = store or SaveStore()
        self.saved = self.store.load()
        self.confirm_new = False

    def begin(self):
        state = Campaign()
        self.store.save(state)
        self.next_scene = Play(campaign=state, store=self.store)

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN or self.next_scene:
            return
        if self.confirm_new:
            if event.key == pygame.K_RETURN:
                self.begin()
            elif event.key == pygame.K_ESCAPE:
                self.confirm_new = False
            return
        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
            if self.saved and not self.saved.finished:
                self.next_scene = Play(campaign=self.saved, store=self.store)
            elif self.saved and self.saved.finished:
                self.next_scene = End(self.saved, self.store)
            else:
                self.begin()
        elif event.key == pygame.K_n:
            if self.saved:
                self.confirm_new = True
            else:
                self.begin()

    def draw(self, canvas):
        canvas.blit(picture("background/Livingroom.png"), (0, 0))
        shade(canvas, 205)
        label(canvas, "OLD TECH", 320, 56, 64, GOLD, True)
        label(canvas, "O N E   L A S T   D E L I V E R Y", 320, 117, 20, MINT, True)
        paragraph(canvas, "An old robot. A quiet house. A promise worth keeping.", 140, 161, 370, 21)
        text = "ENTER  continue delivery" if self.saved and not self.saved.finished else "ENTER  begin delivery"
        if self.saved and self.saved.finished:
            text = "ENTER  revisit ending"
        label(canvas, text, 320, 225, 24, PAPER, True)
        label(canvas, "N  new delivery", 320, 259, 19, MUTED, True)
        label(canvas, "Move: arrows / A D    Jump: Up / W / Space    Use: E", 320, 309, 17, MUTED, True)
        if self.store.error:
            label(canvas, self.store.error, 320, 337, 16, GOLD, True)
        if self.confirm_new:
            panel(canvas, "A new promise?", "Start a new delivery and replace the saved one?", "ENTER start new  /  ESC keep save")


class Play(Scene):
    def __init__(self, levelnum=0, campaign=None, store=None, intro=True):
        super().__init__()
        self.state = campaign or Campaign()
        self.levelnum = self.state.room if campaign else levelnum
        self.state.room = self.levelnum
        self.store = store or SaveStore()
        self.data = levels.LEVELS[self.levelnum]
        self.story = levels.ROOMS[self.levelnum]
        self.background = picture(self.data["background"])
        self.star_img = pygame.transform.scale(picture("background/star.png"), (24, 24))
        self.star = pygame.Rect(*self.data["goalpos"], 32, 32)
        self.edges = [pygame.Rect(-50, -1000, 50, 3000), pygame.Rect(WIDTH, -1000, 50, 3000)]
        self.robot = player.Player(self.data["start_pos"], self.data["car_size"], self.levelnum)
        self.darkness = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self.dialog = None
        self.notice = ""
        self.notice_timer = 0
        self.frames = self.collect_timer = 0
        self.debug = False
        self.refresh_geometry()
        self.sync_modules()
        if self.levelnum in self.state.repaired and self.levelnum != 4:
            self.robot.teleport(self.story["checkpoint"])
        if intro:
            title, body, note = self.story["intro"]
            self.say(title, body, note=note)
        if self.store.error:
            self.notify(self.store.error)

    def refresh_geometry(self):
        self.walls, self.platforms, self.new_platforms, self.ramps = levels.geometry(
            self.levelnum, self.levelnum in self.state.repaired)

    def sync_modules(self):
        self.robot.can_jump = "jump" in self.state.equipped
        self.robot.can_run = "drive" in self.state.equipped

    def persist(self):
        if not self.store.save(self.state):
            self.notify(self.store.error)

    def notify(self, message):
        self.notice, self.notice_timer = message, 240

    def say(self, title, body, note="", confirm=None):
        self.robot.jump_request = False
        self.robot.jump_buffer = 0
        self.dialog = (title, body, note, confirm)

    def near(self, point, radius=48):
        return math.dist(self.robot.rect.center, (point[0], point[1] - 22)) <= radius

    def interaction(self):
        if self.levelnum == 0 and "lamp" not in self.state.owned and self.near((111, 305)):
            return "salvage", "E  salvage lamp / scanner"
        if self.near(self.story["device"]):
            if self.levelnum not in self.state.repaired:
                return "device", "E  " + self.story["device_name"]
            if self.levelnum == 4:
                return "deliver", "E  deliver the brass star"
        if self.levelnum not in self.state.memories and self.near(self.story["memory"]):
            return "memory", "E  read memory" if "lamp" in self.state.equipped else "Memory: connect scanner [3]"
        return None, ""

    def interact(self):
        kind, _ = self.interaction()
        if kind == "salvage":
            self.state.salvage_lamp()
            self.persist()
            self.say("A little more light", "A working lamp, with Miri's scanner taped to its side. Three parts, but only two power sockets.", note="1 springs   2 motor   3 scanner. Disconnect one before connecting another. Swap while standing on a surface.")
        elif kind == "memory":
            if "lamp" not in self.state.equipped:
                self.notify("Connect the scanner [3] to read this memory.")
                return
            self.state.memories.add(self.levelnum)
            self.persist()
            self.say("Memory recovered", self.story["memory_text"], note="Saved in your journal [J]. Memories change the ending, never block the path.")
        elif kind == "device":
            required = self.story["required"]
            if self.levelnum == 0 and "lamp" not in self.state.owned:
                self.notify("Collect the lamp on the floor first. You will need it later.")
            elif required not in self.state.equipped:
                self.notify(f"Connect {MODULE_NAMES[required]} first. Keys 1 / 2 / 3 switch parts.")
            elif self.story["donate"]:
                ability = "sprint" if required == "drive" else "jump"
                route = "bridge across the sink" if required == "drive" else "walking ramp over the boxes"
                self.say("Leave a part of yourself?", f"Dock your {MODULE_NAMES[required].lower()} here permanently? You will no longer {ability}. This powers a {route}.", note="Your delivery will remain possible. R recalls you to safety.", confirm=self.repair)
            else:
                self.repair()
        elif kind == "deliver":
            self.begin_exit()
        else:
            self.notify(self.story["objective"])

    def repair(self):
        if not self.state.repair(self.levelnum):
            return
        self.sync_modules()
        self.refresh_geometry()
        # A new ramp can overlap the robot at the console. Move onto a known safe pad.
        if self.story["donate"]:
            self.robot.teleport(self.story["checkpoint"])
        self.persist()
        self.say("A way forward", self.story["repaired_text"], note="Follow the glowing star." if self.levelnum != 4 else "Press E beside Bear to finish the delivery.")

    def recall(self):
        position = self.story["checkpoint"] if self.levelnum in self.state.repaired else self.data["start_pos"]
        self.robot.teleport(position)
        self.notify("Recalled safely. Repairs and memories are kept.")

    def begin_exit(self):
        if self.collect_timer or self.levelnum not in self.state.repaired:
            return
        self.robot.start_collect()
        self.collect_timer = 48

    def handle_event(self, event):
        if self.next_scene or event.type != pygame.KEYDOWN:
            return
        if self.dialog:
            _, _, _, confirm = self.dialog
            if confirm:
                if event.key == pygame.K_RETURN:
                    self.dialog = None
                    confirm()
                elif event.key == pygame.K_ESCAPE:
                    self.dialog = None
            elif event.key in (pygame.K_RETURN, pygame.K_e, pygame.K_ESCAPE):
                self.dialog = None
            return
        if event.key == pygame.K_ESCAPE:
            self.next_scene = Pause(self)
            return
        if self.collect_timer:
            return
        if event.key == pygame.K_j:
            self.next_scene = Pause(self, journal=True)
        elif event.key == pygame.K_r:
            self.recall()
        elif event.key == pygame.K_F1:
            self.debug = not self.debug
        elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
            if not self.robot.onground:
                self.notify("Land on a surface before switching parts.")
            else:
                self.notify(self.state.toggle(MODULES[event.key - pygame.K_1]))
                self.sync_modules()
                self.persist()
        elif event.key == pygame.K_e:
            self.interact()
        else:
            self.robot.handle_event(event)

    def update(self, keys=None):
        if self.dialog or self.next_scene:
            return
        self.frames += 1
        self.notice_timer = max(0, self.notice_timer - 1)
        if self.collect_timer:
            self.collect_timer -= 1
            if not self.collect_timer:
                self.state.advance()
                self.persist()
                self.next_scene = End(self.state, self.store) if self.state.finished else Play(campaign=self.state, store=self.store)
            return
        if keys is None:
            keys = pygame.key.get_pressed()
        self.robot.update(keys, self.walls + self.edges, self.platforms)
        if self.robot.rect.top > HEIGHT or (self.levelnum == 2 and 367 < self.robot.rect.centerx < 500 and self.robot.rect.bottom > 310):
            self.recall()
        if self.levelnum != 4 and self.robot.rect.colliderect(self.star):
            if self.levelnum in self.state.repaired:
                self.begin_exit()
            else:
                self.notify("Restore the room's device before following the star.")

    def draw_darkness(self, canvas):
        if self.levelnum < 3:
            return
        radius = 115 if "lamp" in self.state.equipped else 51
        self.darkness.fill((5, 10, 21, 220))
        for extra, alpha in ((28, 170), (18, 115), (9, 55), (0, 0)):
            pygame.draw.circle(self.darkness, (0, 0, 0, alpha), self.robot.rect.center, radius + extra)
        if self.levelnum in self.state.repaired:
            for position in ((365, 275), (560, 175)) if self.levelnum == 3 else ((76, 105),):
                pygame.draw.circle(self.darkness, (0, 0, 0, 40), position, 65)
        canvas.blit(self.darkness, (0, 0))

    def draw(self, canvas):
        canvas.blit(self.background, (0, 0))
        for rect in self.new_platforms:
            pygame.draw.rect(canvas, (49, 87, 86), rect)
            pygame.draw.line(canvas, MINT, rect.topleft, rect.topright, 2)
        for start, end in self.ramps:
            pygame.draw.line(canvas, (58, 83, 80), start, end, 7)
            pygame.draw.line(canvas, MINT, start, end, 2)
        x, y = self.story["device"]
        repaired = self.levelnum in self.state.repaired
        color = MINT if repaired else GOLD
        pygame.draw.rect(canvas, INK, (x - 11, y - 29, 22, 29), border_radius=3)
        pygame.draw.rect(canvas, color, (x - 11, y - 29, 22, 29), 1, border_radius=3)
        label(canvas, "+" if repaired else "!", x, y - 27, 23, color, True)
        if self.levelnum == 0 and "lamp" not in self.state.owned:
            pygame.draw.circle(canvas, MINT, (111, 285), 8)
            pygame.draw.circle(canvas, PAPER, (111, 285), 3)
        self.robot.draw(canvas)
        self.draw_darkness(canvas)
        # Beacons remain visible in darkness; memories become legible with the scanner.
        pygame.draw.circle(canvas, color, (x, y - 22), 3)
        mx, my = self.story["memory"]
        if self.levelnum not in self.state.memories:
            if "lamp" in self.state.equipped:
                pygame.draw.polygon(canvas, MINT, [(mx, my - 29), (mx + 6, my - 23), (mx, my - 17), (mx - 6, my - 23)], 2)
            elif self.near(self.story["memory"], 70):
                pygame.draw.circle(canvas, MUTED, (mx, my - 23), 2)
        if not self.collect_timer:
            target = self.star.topleft if self.levelnum != 4 else (49, 91)
            if repaired:
                glow = pygame.Surface((42, 42), pygame.SRCALPHA)
                pygame.draw.circle(glow, (*GOLD, 35 + int(15 * math.sin(self.frames / 15))), (21, 21), 20)
                canvas.blit(glow, (target[0] - 9, target[1] - 9))
                canvas.blit(self.star_img, target)
            else:
                pygame.draw.circle(canvas, MUTED, (target[0] + 12, target[1] + 12), 7, 1)
        if self.debug:
            for rect in self.walls:
                pygame.draw.rect(canvas, (255, 80, 90), rect, 1)
            for rect in self.platforms:
                pygame.draw.rect(canvas, MINT, rect, 1)
            pygame.draw.rect(canvas, GOLD, self.robot.rect, 1)
        pygame.draw.rect(canvas, INK, (0, 0, WIDTH, 20))
        label(canvas, f"{self.levelnum + 1}/5  {self.data['boxes'].name.upper()}  /  {self.story['title']}", 9, 3, 16, GOLD)
        label(canvas, f"MEMORIES {len(self.state.memories)}/5", 531, 3, 16, MINT)
        pygame.draw.rect(canvas, INK, (0, 330, WIDTH, 30))
        for i, (key, name) in enumerate(zip(MODULES, ("SPRINGS", "MOTOR", "SCANNER"))):
            x = 8 + i * 126
            active = key in self.state.equipped
            color = MINT if active else MUTED if key in self.state.owned else (91, 102, 115)
            pygame.draw.rect(canvas, color, (x, 336, 8, 8), 0 if active else 1)
            label(canvas, f"{i + 1} {name}", x + 13, 335, 16, color)
        label(canvas, "E use  R recall  J journal  Esc pause", 393, 336, 15, MUTED)
        if self.notice_timer:
            message_lines = lines(self.notice, 598, 18)
            for i, line in enumerate(message_lines):
                width = font(18).size(line)[0] + 16
                pygame.draw.rect(canvas, INK, ((WIDTH - width) // 2, 27 + i * 19, width, 19), border_radius=4)
                label(canvas, line, 320, 28 + i * 19, 18, GOLD, True)
        kind, prompt = self.interaction()
        if kind and not self.collect_timer:
            width = font(17).size(prompt)[0] + 16
            px = max(width // 2 + 4, min(WIDTH - width // 2 - 4, self.robot.rect.centerx))
            py = max(68, min(298, self.robot.rect.top - 23))
            pygame.draw.rect(canvas, INK, (px - width // 2, py - 2, width, 20), border_radius=4)
            label(canvas, prompt, px, py, 17, GOLD, True)
        if self.dialog:
            title, body, note, confirm = self.dialog
            panel(canvas, title, body, "ENTER leave part  /  ESC keep it" if confirm else "ENTER / E to continue", note)


class Pause(Scene):
    def __init__(self, play, journal=False):
        super().__init__()
        self.play = play
        self.journal = journal
        self.page = 0

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN or self.next_scene:
            return
        if event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
            self.next_scene = self.play
        elif event.key == pygame.K_q:
            self.play.persist()
            self.next_scene = Menu(self.play.store)
        elif event.key == pygame.K_j:
            self.journal = not self.journal
        elif event.key in (pygame.K_LEFT, pygame.K_RIGHT):
            self.page = (self.page + (1 if event.key == pygame.K_RIGHT else -1)) % 5

    def draw(self, canvas):
        self.play.draw(canvas)
        if self.journal:
            text = levels.ROOMS[self.page]["memory_text"] if self.page in self.play.state.memories else "This memory is still in the house. Connect the scanner and press E beside a mint-colored diamond. Memories are optional; each room closes behind you."
            panel(canvas, f"Journal / {levels.LEVELS[self.page]['boxes'].name}", text, "LEFT / RIGHT pages   J controls   ESC resume", note=f"Recovered {len(self.play.state.memories)} of 5 memories.")
        else:
            panel(canvas, "Delivery paused", self.play.story["objective"], "ESC / ENTER resume    J memories    Q save & menu", note="Arrows / A D move. Up / W / Space jump. Shift sprint.\n1 springs / 2 motor / 3 scanner: two sockets. E use. R recall.")


class End(Scene):
    def __init__(self, campaign=None, store=None):
        super().__init__()
        self.state = campaign or Campaign()
        self.store = store or SaveStore()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self.next_scene = Menu(self.store)

    def draw(self, canvas):
        canvas.blit(picture("background/Bedroom.png"), (0, 0))
        shade(canvas, 205)
        # Pip and the delivered keepsake remain together in the final tableau.
        lamp = pygame.Surface((140, 140), pygame.SRCALPHA)
        pygame.draw.circle(lamp, (*GOLD, 28), (70, 70), 66)
        canvas.blit(lamp, (-25, 30))
        canvas.blit(picture("character/idle5.png").subsurface((0, 0, 64, 64)), (47, 65))
        canvas.blit(pygame.transform.scale(picture("background/star.png"), (20, 20)), (36, 102))
        label(canvas, "PROMISE KEPT", 320, 47, 46, GOLD, True)
        text = "Bear has his star. The kitchen hums. A light reaches across the hall. Pip rests beside an old friend."
        if len(self.state.memories) == 5:
            text += "\nWith every memory restored, Pip remembers: it was never just a machine in this house. It was family."
        else:
            text += "\nSome memories have faded. The promise did not. Old things still have love to give."
        paragraph(canvas, text, 112, 111, 416, 23)
        label(canvas, f"{len(self.state.memories)} / 5 memories carried home", 320, 276, 21, MINT, True)
        label(canvas, "ENTER  return to menu", 320, 316, 19, MUTED, True)
