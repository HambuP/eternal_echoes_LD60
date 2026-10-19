"""Fixed 60 Hz movement. Game scenes and route tests use the same simulation."""
import pygame
from assets import picture, ROOT

GRAVITY = 0.3
JUMP_STRENGTH = 7.4
JUMP_CUT = 2
MAX_FALL = 10
WALK_SPEED = 3
RUN_SPEED = 4
STEP_HEIGHT = 8
ANIM_SPEED = 0.22
SPRITE = 64
COYOTE_FRAMES = 6
BUFFER_FRAMES = 7


def cut_frames(path, count, start=0):
    sheet = picture(path)
    return [sheet.subsurface(pygame.Rect(SPRITE * (start + i), 0, SPRITE, SPRITE))
            for i in range(count)]


class Player:
    def __init__(self, start_pos, size, levelnum, can_jump=True, can_run=True):
        n = str(levelnum + 1)
        self.can_jump, self.can_run = can_jump, can_run
        self.rect = pygame.Rect(*start_pos, *size)
        self.rect_draw = pygame.Rect(0, 0, SPRITE, SPRITE)
        self.posy = float(self.rect.y)
        idle = cut_frames(f"character/idle{n}.png", 1)
        walk = cut_frames(f"character/walk{n}.png", 8)
        run_path = f"character/run{n}.png"
        jump_path = f"character/jump{n}.png"
        run = cut_frames(run_path, 8) if (ROOT / run_path).exists() else walk
        jump = cut_frames(jump_path, 1, 1) if (ROOT / jump_path).exists() else idle
        self.collect_frame = cut_frames(f"character/collect{n}.png", 1)[0]
        self.animations = [idle, walk, run, jump]
        self.animationtime = 0
        self.current = idle[0]
        self.dx = self.dy = 0
        self.onground = False
        self.right = True
        self.jump_request = False
        self.jump_buffer = self.coyote = 0
        self.collecting = False
        self.sync_sprite()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_UP, pygame.K_w, pygame.K_SPACE):
            self.jump_request = True

    def sync_sprite(self):
        self.rect_draw.midbottom = self.rect.midbottom

    def teleport(self, position):
        self.rect.topleft = position
        self.posy = float(self.rect.y)
        self.dx = self.dy = 0
        self.jump_request = self.collecting = self.onground = False
        self.jump_buffer = self.coyote = 0
        self.sync_sprite()

    def start_collect(self):
        self.collecting = True
        self.current = self.collect_frame

    @staticmethod
    def is_free(rect, walls):
        return rect.collidelist(walls) == -1

    @staticmethod
    def standing_on(rect, walls, platforms):
        below = rect.move(0, 1)
        return below.collidelist(walls) != -1 or any(
            below.colliderect(p) and rect.bottom <= p.top for p in platforms)

    def update(self, keys, walls, platforms):
        if self.collecting:
            return
        was_onground = self.onground
        self.animationtime += ANIM_SPEED
        self.coyote = COYOTE_FRAMES if self.onground else max(0, self.coyote - 1)
        self.jump_buffer = BUFFER_FRAMES if self.jump_request else max(0, self.jump_buffer - 1)
        self.jump_request = False
        if self.jump_buffer and self.coyote and self.can_jump:
            self.dy = JUMP_STRENGTH
            self.onground = False
            self.coyote = self.jump_buffer = 0
        running = self.can_run and (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT])
        speed = RUN_SPEED if running else WALK_SPEED
        direction = int(bool(keys[pygame.K_RIGHT] or keys[pygame.K_d])) - int(bool(keys[pygame.K_LEFT] or keys[pygame.K_a]))
        self.dx = direction * speed
        if direction:
            self.right = direction > 0
        anim = (2 if running else 1) if direction else 0
        self.rect.x += self.dx
        for wall in walls:
            if self.rect.colliderect(wall):
                lift = self.rect.bottom - wall.top
                if self.dy <= 0 and 0 < lift <= STEP_HEIGHT and self.is_free(self.rect.move(0, -lift), walls):
                    self.rect.y -= lift
                    self.posy = self.rect.y
                elif self.dx > 0:
                    self.rect.right = wall.left
                elif self.dx < 0:
                    self.rect.left = wall.right
        for p in platforms:
            if self.rect.colliderect(p):
                lift = self.rect.bottom - p.top
                if self.dy <= 0 and 0 < lift <= STEP_HEIGHT and self.is_free(self.rect.move(0, -lift), walls):
                    self.rect.y -= lift
                    self.posy = self.rect.y
        previous_bottom = self.rect.bottom
        self.dy = max(-MAX_FALL, self.dy - GRAVITY)
        self.posy -= self.dy
        self.rect.y = round(self.posy)
        falling = self.dy < 0
        for wall in walls:
            if self.rect.colliderect(wall):
                if self.dy > 0:
                    self.rect.top = wall.bottom
                else:
                    self.rect.bottom = wall.top
                self.posy = self.rect.y
                self.dy = 0
        if falling:
            # Highest crossed surface wins, independently of declaration order.
            for p in sorted(platforms, key=lambda p: p.top):
                if self.rect.colliderect(p) and previous_bottom <= p.top:
                    self.rect.bottom = p.top
                    self.posy = self.rect.y
                    self.dy = 0
        self.onground = self.standing_on(self.rect, walls, platforms)
        if not self.onground and was_onground and self.dy <= 0:
            for distance in range(1, STEP_HEIGHT + 1):
                test = self.rect.move(0, distance)
                if not self.is_free(test, walls):
                    break
                if self.standing_on(test, walls, platforms):
                    self.rect.y += distance
                    self.posy = self.rect.y
                    self.dy = 0
                    self.onground = True
                    break
        held_jump = keys[pygame.K_UP] or keys[pygame.K_w] or keys[pygame.K_SPACE]
        if not held_jump and self.dy > JUMP_CUT:
            self.dy = JUMP_CUT
        if not self.onground:
            anim = 3
        frames = self.animations[anim]
        self.current = frames[int(self.animationtime) % len(frames)]
        self.sync_sprite()

    def draw(self, canvas):
        canvas.blit(self.current if self.right else pygame.transform.flip(self.current, True, False), self.rect_draw)
