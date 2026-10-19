import pygame
import levels
import player

WIDTH, HEIGHT = 640, 360
STAR_SIZE = 32          # star is scaled to this size (set it to the PNG's real size to avoid scaling)
COLLECT_FRAMES = 60     # how long the robot celebrates after grabbing a star (60 = 1 second)
DARKNESS = 245          # 0-255, how dark it is outside the light circle (255 = pitch black)
LIGHT_SOFTNESS = 0      # 0 = hard edge. Higher = softer edge (number of fading rings)
LIGHT_RING_WIDTH = 3    # pixels per ring when LIGHT_SOFTNESS > 0

show_hitboxes = False   # press F1 in a level to toggle

_fonts = {}


def draw_text(canvas, text, size, y, color=(255, 255, 255)):
    if size not in _fonts:
        _fonts[size] = pygame.font.Font(None, size)
    img = _fonts[size].render(text, False, color)
    canvas.blit(img, img.get_rect(center=(WIDTH // 2, y)))


class Scene:
    """Every screen has these. To change screens, set self.next_scene."""
    def __init__(self):
        self.next_scene = None

    def handle_event(self, event):
        pass

    def update(self):
        pass

    def draw(self, canvas):
        pass


class Menu(Scene):
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self.next_scene = Play(0)

    def draw(self, canvas):
        canvas.fill((0, 0, 0))
        draw_text(canvas, "OLD TECH", 64, 140)
        draw_text(canvas, "press ENTER to start", 24, 200, (160, 160, 160))


class Play(Scene):
    def __init__(self, levelnum):
        super().__init__()
        self.levelnum = levelnum
        data = levels.LEVELS[levelnum]

        self.map = data["boxes"]
        # invisible walls on the left and right edges of the screen
        self.edges = [pygame.Rect(-50, -1000, 50, 3000), pygame.Rect(WIDTH, -1000, 50, 3000)]

        self.background = pygame.image.load(data["background"]).convert()
        self.foreground = None
        if data.get("foreground"):
            self.foreground = pygame.image.load(data["foreground"]).convert_alpha()
        self.visibility = data.get("visibility")
        self.darkness = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

        star = pygame.image.load("background/star.png").convert_alpha()
        if star.get_size() != (STAR_SIZE, STAR_SIZE):
            star = pygame.transform.scale(star, (STAR_SIZE, STAR_SIZE))
        self.star_img = star
        self.star = pygame.Rect(data["goalpos"][0], data["goalpos"][1], STAR_SIZE, STAR_SIZE)

        self.robot = player.Player(data["start_pos"], data["car_size"], levelnum, data["jump"], data["run"])
        self.collect_timer = 0

    def handle_event(self, event):
        global show_hitboxes
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.next_scene = Pause(self)
                return
            if event.key == pygame.K_r:
                self.next_scene = Play(self.levelnum)
                return
            if event.key == pygame.K_F1:
                show_hitboxes = not show_hitboxes
        self.robot.handle_event(event)

    def update(self):
        # celebrating after grabbing the star
        if self.collect_timer > 0:
            self.collect_timer -= 1
            if self.collect_timer == 0:
                next_level = self.levelnum + 1
                if next_level < len(levels.LEVELS):
                    self.next_scene = Play(next_level)
                else:
                    self.next_scene = End()
            return

        keys = pygame.key.get_pressed()
        self.robot.update(keys, self.map.walls + self.edges, self.map.platforms)

        if self.robot.rect.top > HEIGHT:            # fell off the map
            self.next_scene = Play(self.levelnum)

        if self.robot.rect.colliderect(self.star):
            self.robot.start_collect()
            self.collect_timer = COLLECT_FRAMES

    def draw_darkness(self, canvas):
        center = self.robot.rect.center
        self.darkness.fill((0, 0, 0, DARKNESS))
        for k in range(LIGHT_SOFTNESS, 0, -1):      # optional soft edge, outer rings darker
            alpha = DARKNESS * k // (LIGHT_SOFTNESS + 1)
            pygame.draw.circle(self.darkness, (0, 0, 0, alpha), center, self.visibility + k * LIGHT_RING_WIDTH)
        pygame.draw.circle(self.darkness, (0, 0, 0, 0), center, self.visibility)
        canvas.blit(self.darkness, (0, 0))

    def draw(self, canvas):
        canvas.blit(self.background, (0, 0))

        if show_hitboxes:
            for wall in self.map.walls:
                pygame.draw.rect(canvas, (255, 0, 0), wall, 1)
            for p in self.map.platforms:
                pygame.draw.rect(canvas, (0, 220, 255), p, 1)
            pygame.draw.rect(canvas, (0, 255, 0), self.robot.rect, 1)

        self.robot.draw(canvas)

        if self.foreground:
            canvas.blit(self.foreground, (0, 0))

        if self.visibility:
            self.draw_darkness(canvas)

        # star is drawn after the darkness so it always shows, like a beacon
        if self.collect_timer == 0:
            canvas.blit(self.star_img, self.star)


class Pause(Scene):
    def __init__(self, play):
        super().__init__()
        self.play = play                             # the frozen level, so we can go back to it
        self.overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self.overlay.fill((0, 0, 0, 170))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                self.next_scene = self.play
            elif event.key == pygame.K_q:
                self.next_scene = Menu()

    def draw(self, canvas):
        self.play.draw(canvas)
        canvas.blit(self.overlay, (0, 0))
        draw_text(canvas, "PAUSED", 56, 150)
        draw_text(canvas, "ESC resume    Q menu", 24, 200, (180, 180, 180))


class End(Scene):
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self.next_scene = Menu()

    def draw(self, canvas):
        canvas.fill((0, 0, 0))
        draw_text(canvas, "THE END", 64, 150)
        draw_text(canvas, "press ENTER", 24, 200, (160, 160, 160))