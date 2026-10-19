"""Route prover: which (x, y) positions can the robot reach in a room with a given set of abilities?

Runs a breadth-first search over the real Player physics (player.py), pressing every
combination of keys each frame, so a position it reports is reachable for real.

Usage:
    python tools/routes.py            # checks every room: star needs its ability, door doesn't
    python tools/routes.py 2 --map    # prints an ASCII map of what is reachable in room 3

Set SDL_VIDEODRIVER=dummy to run without a window.
"""
import os
import sys
from collections import deque

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pygame  # noqa: E402

pygame.init()
pygame.display.set_mode((1, 1))

import levels  # noqa: E402
import player  # noqa: E402

ROOM_W, ROOM_H = 640, 360
EDGES = [pygame.Rect(-50, -1000, 50, 3000), pygame.Rect(ROOM_W, -1000, 50, 3000)]


class Keys:
    def __init__(self, direction, jump_held, run):
        self.direction, self.jump_held, self.run = direction, jump_held, run

    def __getitem__(self, key):
        if key in (pygame.K_RIGHT, pygame.K_d):
            return self.direction > 0
        if key in (pygame.K_LEFT, pygame.K_a):
            return self.direction < 0
        if key in (pygame.K_UP, pygame.K_w, pygame.K_SPACE):
            return self.jump_held
        if key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
            return self.run
        return False


def actions(can_jump, can_run):
    runs = (False, True) if can_run else (False,)
    # (direction, press jump this frame, hold jump, run)
    out = []
    for d in (-1, 0, 1):
        for r in runs:
            out.append((d, False, False, r))
            if can_jump:
                out.append((d, True, True, r))    # press and keep holding
                out.append((d, False, True, r))   # keep holding (full height)
    return out


def snapshot(p):
    return (p.rect.x, p.rect.y, round(p.dy, 2), p.onground, p.coyote, p.jump_buffer)


def restore(p, s):
    p.rect.x, p.rect.y, p.dy, p.onground, p.coyote, p.jump_buffer = s
    p.posx = float(p.rect.x)
    p.posy = float(p.rect.y)
    p.jump_request = False


HOLDS = (3, 8, 40)                      # frames the jump key stays down: hop, medium, full
STEERS = ((1, 1), (1, 0), (0, 1), (-1, -1), (-1, 0), (0, -1), (0, 0))   # direction before / after apex


def jump_macros(can_run):
    out = []
    for before, after in STEERS:
        for run in ((False, True) if can_run else (False,)):
            for hold in HOLDS:
                out.append((before, after, run, hold))
    return out


def fly(p, walls, platforms, before, after, run, hold, positions, limit=160):
    """Press jump now and keep flying until landing. Returns the landing state or None.
    Every mid-air position is added to `positions` (stars can be grabbed in the air)."""
    p.jump_request = True
    for frame in range(limit):
        d = before if p.dy > 0 or frame == 0 else after
        p.update(Keys(d, frame < hold, run), walls, platforms)
        p.jump_request = False
        if p.rect.top > ROOM_H or p.rect.right < -60 or p.rect.left > ROOM_W + 60:
            return None
        positions.add((p.rect.x, p.rect.y))
        if p.onground and frame > 0:
            return snapshot(p)
    return None


def reachable(room, can_jump, can_run, walls=None, platforms=None, start=None, jump_every=2,
              wear=None, open_exit=False):
    """Return the set of reachable rect top-left positions (x, y), searching ground
    positions with single walking frames and whole jump arcs as moves."""
    data = levels.LEVELS[room]
    edges = list(EDGES)
    if open_exit and data["exit"] == "left":
        edges = [EDGES[1]]
    elif open_exit and data["exit"] == "right":
        edges = [EDGES[0]]
    walls = (walls if walls is not None else list(data["boxes"].walls)) + edges
    platforms = platforms if platforms is not None else list(data["boxes"].platforms)
    p = player.Player(start or data["start_pos"], data["car_size"], room, can_jump, can_run,
                      wear=room if wear is None else wear)
    macros = jump_macros(can_run) if can_jump else []
    for _ in range(30):
        p.update(Keys(0, False, False), walls, platforms)
    first = snapshot(p)
    seen = {first[:2]}
    queue = deque([first])
    positions = set()
    while queue:
        s = queue.popleft()
        positions.add((s[0], s[1]))
        moves = []
        for d in (-1, 1):
            for run in ((False, True) if can_run else (False,)):
                restore(p, s)
                p.update(Keys(d, False, run), walls, platforms)
                # walking off an edge: fall until we land somewhere
                for _ in range(160):
                    if p.onground or p.rect.top > ROOM_H or p.rect.right < -60 or p.rect.left > ROOM_W + 60:
                        break
                    positions.add((p.rect.x, p.rect.y))
                    p.update(Keys(d, False, run), walls, platforms)
                if p.onground:
                    moves.append(snapshot(p))
        if macros and s[0] % jump_every == 0:
            for before, after, run, hold in macros:
                restore(p, s)
                landing = fly(p, walls, platforms, before, after, run, hold, positions)
                if landing:
                    moves.append(landing)
        for n in moves:
            if n[:2] not in seen:
                seen.add(n[:2])
                queue.append(n)
    return positions


def touches(positions, target, size):
    """Does any reachable robot rect overlap the target rect?"""
    w, h = size
    t = pygame.Rect(target)
    return any(pygame.Rect(x, y, w, h).colliderect(t) for x, y in positions)


def ascii_map(positions, room, cell=8):
    data = levels.LEVELS[room]
    grid = [[" "] * (ROOM_W // cell) for _ in range(ROOM_H // cell)]
    for r in data["boxes"].walls:
        for gx in range(r.left // cell, min(ROOM_W, r.right) // cell):
            for gy in range(r.top // cell, min(ROOM_H, r.bottom) // cell):
                grid[gy][gx] = "#"
    for r in data["boxes"].platforms:
        for gx in range(r.left // cell, min(ROOM_W, r.right) // cell):
            grid[r.top // cell][gx] = "="
    for x, y in positions:                       # mark where the robot's feet can be
        gy, gx = (y + data["car_size"][1] - 1) // cell, (x + data["car_size"][0] // 2) // cell
        if 0 <= gy < len(grid) and 0 <= gx < len(grid[0]) and grid[gy][gx] == " ":
            grid[gy][gx] = "."
    sx, sy = data["goalpos"]
    grid[sy // cell][sx // cell] = "*"
    return "\n".join("".join(row) for row in grid)


def check_room(i):
    data = levels.LEVELS[i]
    size = data["car_size"]
    start_abilities = data["abilities"]
    lost = data["loses"]
    after = {k: (v and k != lost) for k, v in start_abilities.items()}
    star = pygame.Rect(*data["goalpos"], 32, 32)
    door = levels.exit_zone(i)
    full = reachable(i, start_abilities["jump"], start_abilities["run"])
    star_ok = touches(full, star, size)
    reduced = reachable(i, after["jump"], after["run"], wear=i + 1)
    star_without = touches(reduced, star, size) if lost in ("jump", "run") and data.get("gated", True) else None
    # The way back: from the star, with the reduced abilities, can we reach the door?
    feet = sorted((x, y) for x, y in full if pygame.Rect(x, y, *size).colliderect(star))
    # wherever the robot was when it touched the star, the door must still be reachable
    samples = feet[:: max(1, len(feet) // 6)] if feet else []
    door_ok = bool(samples) and all(
        touches(reachable(i, after["jump"], after["run"], start=start, wear=i + 1, open_exit=True), door, size)
        for start in samples)
    print(f"Room {i + 1} {data['boxes'].name}: star reachable={star_ok}, "
          f"star reachable WITHOUT {lost}={star_without}, door reachable after loss={door_ok}")
    return star_ok and door_ok and (star_without is not True)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if args:
        room = int(args[0])
        d = levels.LEVELS[room]
        if "--map" in sys.argv:
            a = d["abilities"]
            print(ascii_map(reachable(room, a["jump"], a["run"]), room))
        else:
            check_room(room)
    else:
        ok = all(check_room(i) for i in range(len(levels.LEVELS)))
        print("ALL ROOMS OK" if ok else "SOME ROOMS FAIL")
        sys.exit(0 if ok else 1)
