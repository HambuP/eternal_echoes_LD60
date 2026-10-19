import pygame

# ---------- tuning: play with these ----------
GRAVITY = 0.3
JUMP_STRENGTH = 7       # upward speed when a jump starts
JUMP_CUT = 2            # upward speed when you let go of UP early (short hop)
MAX_FALL = 10           # fastest falling speed
WALK_SPEED = 3
RUN_SPEED = 4
STEP_HEIGHT = 8         # the robot walks up anything this tall automatically (slopes, small bumps)
ANIM_SPEED = 0.3        # animation frames per game frame
SPRITE = 64             # size of one frame in the sprite sheets
WALK_FRAMES = 8
RUN_FRAMES = 8


def overlap(rect1, rect2):
    return rect1.colliderect(rect2)


def cut_frames(path, count, start=0):
    """Loads a sprite sheet and cuts `count` 64x64 frames from the top row."""
    sheet = pygame.image.load(path).convert_alpha()
    return [sheet.subsurface(pygame.Rect(SPRITE * (start + i), 0, SPRITE, SPRITE)) for i in range(count)]


class Player:
    def __init__(self, start_pos, size, levelnum, can_jump, can_run):
        n = str(levelnum + 1)
        self.can_jump = can_jump
        self.can_run = can_run

        self.rect = pygame.Rect(start_pos[0], start_pos[1], size[0], size[1])   # hitbox
        self.rect_draw = pygame.Rect(self.rect.x, self.rect.y, SPRITE, SPRITE)  # where the sprite is drawn
        self.posy = float(self.rect.y)

        # animations: only load run / jump if this level has them
        idle = cut_frames("character/idle" + n + ".png", 1)
        walk = cut_frames("character/walk" + n + ".png", WALK_FRAMES)
        run = cut_frames("character/run" + n + ".png", RUN_FRAMES) if can_run else walk
        jump = cut_frames("character/jump" + n + ".png", 1, start=1) if can_jump else idle
        self.collect_frame = cut_frames("character/collect" + n + ".png", 1)[0]

        self.animations = [idle, walk, run, jump]   # 0 idle, 1 walk, 2 run, 3 in the air
        self.animationtime = 0
        self.current = idle[0]

        self.dx = 0
        self.dy = 0              # positive = going up
        self.onground = False
        self.right = True
        self.jump_request = False
        self.collecting = False

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_UP:
            self.jump_request = True

    def start_collect(self):
        """Freezes the robot and shows the collect frame (green button)."""
        self.collecting = True
        self.current = self.collect_frame

    def is_free(self, rect, walls):
        return rect.collidelist(walls) == -1

    def standing_on(self, rect, walls, platforms):
        """True if there's a wall, or the top of a one-way platform, right under this rect."""
        below = rect.move(0, 1)
        if below.collidelist(walls) != -1:
            return True
        for p in platforms:
            if below.colliderect(p) and rect.bottom <= p.top:
                return True
        return False

    def update(self, keys, walls, platforms):
        if self.collecting:
            return

        was_onground = self.onground
        self.animationtime += ANIM_SPEED
        anim = 0

        # ---- jump ----
        if self.jump_request and self.onground and self.can_jump:
            self.dy = JUMP_STRENGTH
            self.onground = False
        self.jump_request = False

        # ---- horizontal input ----
        running = self.can_run and (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT])
        speed = RUN_SPEED if running else WALK_SPEED

        self.dx = 0
        if keys[pygame.K_LEFT]:
            self.dx = -speed
            self.right = False
        if keys[pygame.K_RIGHT]:
            self.dx = speed
            self.right = True
        if self.dx != 0:
            anim = 2 if running else 1

        # ---- horizontal move + collisions (with step-up for slopes) ----
        self.rect.x += self.dx
        for wall in walls:
            if overlap(wall, self.rect):
                lift = self.rect.bottom - wall.top     # how tall this obstacle is compared to our feet
                if self.dy <= 0 and 0 < lift <= STEP_HEIGHT and self.is_free(self.rect.move(0, -lift), walls):
                    self.rect.y -= lift                # small step: climb on top of it
                    self.posy = self.rect.y
                elif self.dx > 0:
                    self.rect.right = wall.left
                elif self.dx < 0:
                    self.rect.left = wall.right

        # one-way platforms never block sideways, but you can still step up onto them
        for p in platforms:
            if overlap(p, self.rect):
                lift = self.rect.bottom - p.top
                if self.dy <= 0 and 0 < lift <= STEP_HEIGHT and self.is_free(self.rect.move(0, -lift), walls):
                    self.rect.y -= lift
                    self.posy = self.rect.y

        # ---- gravity + vertical collisions ----
        prev_bottom = self.rect.bottom
        self.dy -= GRAVITY
        if self.dy < -MAX_FALL:
            self.dy = -MAX_FALL
        self.posy -= self.dy
        self.rect.y = round(self.posy)

        falling = self.dy < 0
        for wall in walls:
            if overlap(wall, self.rect):
                if self.dy > 0:
                    self.rect.top = wall.bottom
                else:
                    self.rect.bottom = wall.top
                self.posy = self.rect.y
                self.dy = 0

        # one-way platforms only catch you when you fall onto them from above
        if falling:
            for p in platforms:
                if overlap(p, self.rect) and prev_bottom <= p.top:
                    self.rect.bottom = p.top
                    self.posy = self.rect.y
                    self.dy = 0

        # ---- ground check ----
        self.onground = self.standing_on(self.rect, walls, platforms)

        # walking down a slope: snap down small steps instead of falling
        if not self.onground and was_onground and self.dy <= 0:
            for d in range(1, STEP_HEIGHT + 1):
                test = self.rect.move(0, d)
                if not self.is_free(test, walls):
                    break
                if self.standing_on(test, walls, platforms):
                    self.rect.y += d
                    self.posy = self.rect.y
                    self.dy = 0
                    self.onground = True
                    break

        # ---- variable jump height ----
        if not keys[pygame.K_UP] and self.dy > JUMP_CUT:
            self.dy = JUMP_CUT

        # ---- animation ----
        if not self.onground:
            anim = 3
        frames = self.animations[anim]
        self.current = frames[int(self.animationtime) % len(frames)]

        self.rect_draw.x = self.rect.centerx - SPRITE // 2
        self.rect_draw.y = self.rect.bottom - SPRITE

    def draw(self, canvas):
        image = self.current
        if not self.right:
            image = pygame.transform.flip(image, True, False)
        canvas.blit(image, self.rect_draw)