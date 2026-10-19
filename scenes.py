"""Story, interaction, and compact UI for the five-room delivery."""
import math
import pygame
import levels
import player
from assets import picture
from campaign import Campaign, SaveStore, MODULES, MODULE_NAMES
from sound import soundscape

from ui import (WIDTH, HEIGHT, INK, PAPER, MUTED, GOLD, MINT, BORDER,
                font, label, lines, paragraph, shade, panel, card, action,
                actions_row, prompt)


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
        shade(canvas, 210)
        label(canvas, "Old Tech", 320, 59, 64, GOLD, True)
        label(canvas, "One Last Delivery", 320, 122, 27, PAPER, True)
        label(canvas, "A quiet house. A promise worth keeping.", 320, 176, 21, MUTED, True)
        text = "Continue delivery" if self.saved and not self.saved.finished else "Begin delivery"
        if self.saved and self.saved.finished:
            text = "Revisit ending"
        actions_row(canvas, (("Enter", text),), 232)
        if self.saved:
            actions_row(canvas, (("N", "New delivery"),), 271)
        label(canvas, "Controls are available in the pause menu.", 320, 323, 17, MUTED, True)
        if self.store.error:
            pygame.draw.rect(canvas, INK, (0, 315, 640, 45))
            label(canvas, self.store.error, 320, 329, 17, GOLD, True)
        if self.confirm_new:
            panel(canvas, "A new promise?", "Start a new delivery and replace the saved one?",
                  (("Enter", "Start new"), ("Esc", "Keep save")))


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
        soundscape.silence_robot()
        self.robot.jump_request = False
        self.robot.jump_buffer = 0
        self.dialog = (title, body, note, confirm)

    def near(self, point, radius=48):
        return math.dist(self.robot.rect.center, (point[0], point[1] - 22)) <= radius

    def interaction(self):
        if self.levelnum == 0 and "lamp" not in self.state.owned and self.near((111, 305)):
            return "salvage", "Salvage scanner"
        if self.near(self.story["device"]):
            if self.levelnum not in self.state.repaired:
                return "device", ("Wind music box", "Scan desk terminal", "Power sink pump",
                                  "Raise hall lift", "Light Bear's lamp")[self.levelnum]
            if self.levelnum == 4:
                return "deliver", "Deliver the star"
        if self.levelnum not in self.state.memories and self.near(self.story["memory"]):
            return "memory", "Read memory" if "lamp" in self.state.equipped else "Connect scanner"
        return None, ""

    def interact(self):
        kind, _ = self.interaction()
        if kind == "salvage":
            self.state.salvage_lamp()
            self.persist()
            self.say("A little more light", "A working lamp, with Miri's scanner taped to its side. Three parts, but only two power sockets.", note="Use 1, 2, or 3 to switch parts while grounded. Disconnect one before connecting another. Open the pause menu for controls.")
        elif kind == "memory":
            if "lamp" not in self.state.equipped:
                self.notify("Press 3 to connect the scanner and read this memory.")
                return
            self.state.memories.add(self.levelnum)
            self.persist()
            self.say("Memory recovered", self.story["memory_text"], note="Saved in your journal. Press J to read it again. Memories are optional.")
        elif kind == "device":
            required = self.story["required"]
            if self.levelnum == 0 and "lamp" not in self.state.owned:
                self.notify("Collect the lamp on the floor first. You will need it later.")
            elif required not in self.state.equipped:
                self.notify(f"Connect {MODULE_NAMES[required]} first. Use 1, 2, or 3 to switch parts.")
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
        soundscape.silence_robot()
        position = self.story["checkpoint"] if self.levelnum in self.state.repaired else self.data["start_pos"]
        self.robot.teleport(position)
        self.notify("Recalled safely. Repairs and memories are kept.")

    def begin_exit(self):
        if self.collect_timer or self.levelnum not in self.state.repaired:
            return
        soundscape.silence_robot()
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
        previous_x = self.robot.rect.x
        previous_dy = self.robot.dy
        was_grounded, was_right = self.robot.onground, self.robot.right
        self.robot.update(keys, self.walls + self.edges, self.platforms)
        moving = self.robot.rect.x != previous_x
        soundscape.update_robot(
            self.robot, moving=moving, jumped=self.robot.jumped,
            landed=not was_grounded and self.robot.onground and previous_dy < -1.5,
            turned=moving and self.robot.right != was_right)
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

    def draw(self, canvas, show_ui=True):
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
        if not show_ui:
            return
        if self.dialog:
            title, body, note, confirm = self.dialog
            panel(canvas, title, body,
                  (("Enter", "Leave part"), ("Esc", "Keep part")) if confirm else (("Enter", "Continue"),),
                  note)
            return
        # The room name is enough during play; its chapter title lives in the story.
        pygame.draw.rect(canvas, INK, (0, 0, WIDTH, 24))
        label(canvas, f"{self.levelnum + 1} / 5", 14, 6, 17, MUTED)
        label(canvas, self.data['boxes'].name, 68, 5, 20, PAPER)
        memories = f"Memories  {len(self.state.memories)} / 5"
        label(canvas, memories, WIDTH - 14 - font(18).size(memories)[0], 6, 18, MINT)
        pygame.draw.rect(canvas, INK, (0, 328, WIDTH, 32))
        for i, (module, name) in enumerate(zip(MODULES, ("Springs", "Motor", "Scanner"))):
            active = module in self.state.equipped
            color = PAPER if active else MUTED if module in self.state.owned else (94, 110, 122)
            action(canvas, str(i + 1), name, 12 + i * 105, 333, color=color, active=active)
        action(canvas, "J", "Journal", 423, 333, color=MUTED)
        action(canvas, "Esc", "Menu", 533, 333, color=MUTED)
        notice_bottom = 28
        if self.notice_timer:
            wrapped = lines(self.notice, 526, 19)
            width = max(font(19).size(line)[0] for line in wrapped) + 28
            height = len(wrapped) * 23 + 16
            rect = pygame.Rect((WIDTH - width) // 2, 34, width, height)
            pygame.draw.rect(canvas, INK, rect, border_radius=6)
            pygame.draw.rect(canvas, BORDER, rect, 1, border_radius=6)
            paragraph(canvas, self.notice, rect.x + 14, rect.y + 8, 526, 19, GOLD, leading=23)
            notice_bottom = rect.bottom
        kind, text = self.interaction()
        if kind and not self.collect_timer:
            key = "3" if kind == "memory" and "lamp" not in self.state.equipped else "E"
            top = max(notice_bottom + 10, min(286, self.robot.rect.top - 42))
            prompt(canvas, key, text, self.robot.rect.centerx, top)


class Pause(Scene):
    def __init__(self, play, journal=False):
        super().__init__()
        self.play = play
        soundscape.silence_robot()
        self.journal = journal
        self.controls = False
        self.page = play.levelnum

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
            self.controls = False
        elif event.key == pygame.K_h:
            self.controls = not self.controls
            self.journal = False
        elif self.journal and event.key in (pygame.K_LEFT, pygame.K_RIGHT):
            self.page = (self.page + (1 if event.key == pygame.K_RIGHT else -1)) % 5

    def draw(self, canvas):
        self.play.draw(canvas, show_ui=False)
        if self.journal:
            text = levels.ROOMS[self.page]["memory_text"] if self.page in self.play.state.memories else "This memory is still in the house. Connect the scanner and press E beside a mint-colored diamond. Each room closes behind you."
            panel(canvas, levels.LEVELS[self.page]['boxes'].name, text,
                  (("Left / Right", "Browse"), ("J", "Back"), ("Esc", "Resume")),
                  note=f"Memories recovered: {len(self.play.state.memories)} / 5.", eyebrow="Journal")
        elif self.controls:
            card(canvas, "Controls")
            rows = (
                ("Move", "Left / Right   or   A / D"),
                ("Jump", "Up, W, or Space"),
                ("Sprint", "Hold Shift while moving"),
                ("Switch parts", ""),
                ("Interact", "E"),
                ("Recall to safety", "R"),
            )
            for i, (name, binding) in enumerate(rows):
                y = 108 + i * 24
                label(canvas, name, 64, y, 19, PAPER)
                if name == "Switch parts":
                    for key, text, x in (("1", "Springs", 256), ("2", "Motor", 363), ("3", "Scanner", 460)):
                        action(canvas, key, text, x, y - 3, size=17, color=MUTED)
                else:
                    label(canvas, binding, 256, y, 18, MUTED)
            label(canvas, "Two sockets. Switch parts while grounded.", 64, 258, 17, MINT)
            pygame.draw.line(canvas, BORDER, (64, 278), (576, 278))
            actions_row(canvas, (("H", "Back"), ("Esc", "Resume")), 291)
        else:
            card(canvas, "Delivery paused")
            label(canvas, "Current objective", 64, 108, 18, MINT)
            paragraph(canvas, self.play.story["objective"], 64, 137, 512, 22, leading=27)
            action(canvas, "H", "Controls", 64, 218)
            action(canvas, "J", "Memories", 338, 218)
            action(canvas, "M", soundscape.status, 64, 249, color=MUTED)
            pygame.draw.line(canvas, BORDER, (64, 278), (576, 278))
            actions_row(canvas, (("Esc", "Resume"), ("Q", "Save and quit to menu")), 291)


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
        label(canvas, "Promise kept", 320, 47, 46, GOLD, True)
        text = "Bear has his star. The kitchen hums. A light reaches across the hall. Pip rests beside an old friend."
        if len(self.state.memories) == 5:
            text += "\nWith every memory restored, Pip remembers: it was never just a machine in this house. It was family."
        else:
            text += "\nSome memories have faded. The promise did not. Old things still have love to give."
        paragraph(canvas, text, 112, 111, 416, 23)
        label(canvas, f"{len(self.state.memories)} / 5 memories carried home", 320, 276, 21, MINT, True)
        actions_row(canvas, (("Enter", "Return to menu"),), 316)
