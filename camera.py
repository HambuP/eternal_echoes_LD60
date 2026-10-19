"""A close camera that follows the robot with a little lag and look-ahead."""
import random
import pygame


class Camera:
    def __init__(self, view_size, room_size):
        self.vw, self.vh = view_size
        self.rw, self.rh = room_size
        self.x = self.y = 0.0
        self.lead = 0.0
        self.shake = 0
        self.hold = 0                 # frames to stay still (star pickup)
        self.lerp = 0.08

    def target(self, rect, facing_right):
        want = 36 if facing_right else -36
        self.lead += (want - self.lead) * 0.04
        tx = rect.centerx + self.lead - self.vw / 2
        ty = rect.centery - 12 - self.vh / 2
        return tx, ty

    def snap(self, rect, facing_right):
        self.lead = 36 if facing_right else -36
        self.x, self.y = self.target(rect, facing_right)
        self.clamp()

    def clamp(self):
        self.x = max(0, min(self.rw - self.vw, self.x))
        self.y = max(0, min(self.rh - self.vh, self.y))

    def update(self, rect, facing_right):
        if self.hold:
            self.hold -= 1
            return
        tx, ty = self.target(rect, facing_right)
        self.x += (tx - self.x) * self.lerp
        self.y += (ty - self.y) * self.lerp * 1.25
        self.clamp()
        self.shake = max(0, self.shake - 1)

    def kick(self, frames=8):
        self.shake = max(self.shake, frames)

    def view(self):
        """The room rectangle currently on screen."""
        s = self.shake
        dx = random.randint(-s, s) // 3 if s else 0
        dy = random.randint(-s, s) // 3 if s else 0
        return pygame.Rect(round(self.x) + dx, round(self.y) + dy, self.vw, self.vh)
