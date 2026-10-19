"""Pure data: one entry per room.

Each room: where you start, where the star is, which abilities you still have when
you walk in, which one dies when you grab the star, and where the door out is.
The star sits at the end of the route that needs the dying ability; the door is
reachable without it. `python tools/routes.py` proves both claims against the physics.
"""
import math
import pygame

ROOM_W, ROOM_H = 640, 360


def staircase(start, end, step):
    """Turns a slope from start to end into thin columns, each `step` pixels taller than the last."""
    (x1, y1), (x2, y2) = start, end
    if x2 < x1:                                   # always build left to right
        (x1, y1), (x2, y2) = (x2, y2), (x1, y1)
    bottom = max(y1, y2)                          # columns go down to the lower end
    count = max(1, math.ceil(abs(y2 - y1) / step))
    width = (x2 - x1) / count
    columns = []
    for i in range(count):
        left = round(x1 + i * width)
        right = round(x1 + (i + 1) * width)
        frac = (i + 1) / count if y2 < y1 else i / count   # the high end meets its point exactly
        top = round(y1 + (y2 - y1) * frac)
        if bottom - top > 0:
            columns.append(pygame.Rect(left, top, right - left, bottom - top))
    return columns


class Map:
    def __init__(self, name):
        self.name = name
        self.solids = []          # normal boxes
        self.oneways = []         # one-way platforms: you pass through from below, stand on top
        self.slope_solids = []
        self.slope_oneways = []

    def create_wall(self, point, size):
        self.solids.append(pygame.Rect(point[0], point[1], size[0], size[1]))

    def create_platform(self, point, size):
        self.oneways.append(pygame.Rect(point[0], point[1], size[0], size[1]))

    def create_slope(self, start, end, step=6, oneway=False):
        columns = staircase(start, end, step)
        if oneway:
            self.slope_oneways.extend(columns)
        else:
            self.slope_solids.extend(columns)

    @property
    def walls(self):
        return self.solids + self.slope_solids

    @property
    def platforms(self):
        return self.oneways + self.slope_oneways


map1 = Map("Living room")
map1.create_wall((0, 305), (640, 63))     # floor
map1.create_wall((302, 130), (111, 20))   # wall shelf
map1.create_wall((38, 60), (89, 10))      # top of left picture frame
map1.create_wall((188, 100), (75, 10))    # top of right picture frame
map1.create_wall((366, 260), (69, 43))    # small round table
map1.create_wall((469, 200), (171, 97))   # desk
map1.create_wall((539, 174), (36, 28))    # phone on the desk
map1.create_wall((575, 140), (65, 65))    # TV

map2 = Map("Study")
map2.create_wall((0, 320), (640, 40))     # floor
map2.create_wall((65, 51), (185, 100))    # bookcase
map2.create_wall((143, 45), (53, 6))      # book on top of the bookcase
map2.create_wall((390, 96), (90, 17))    # upper shelf
map2.create_wall((469, 120), (111, 18))   # lower shelf: 102 px above the table, only a sprint jump gets up
map2.create_wall((290, 302), (101, 18))   # wood pile, base
map2.create_wall((320, 281), (50, 21))    # wood pile, peak
map2.create_wall((406, 222), (234, 24))   # table top
map2.create_wall((418, 246), (20, 74))    # table front leg
map2.create_wall((621, 175), (19, 222))   # the book at the right edge to the shelves

map3 = Map("Kitchen")
map3.create_wall((0, 325), (640, 35))     # floor
map3.create_wall((0, 74), (74, 18))       # shelf 1
map3.create_wall((2, 38), (28, 36))       # vase on shelf 1
map3.create_wall((135, 73), (83, 18))     # shelf 2
map3.create_wall((286, 73), (81, 18))     # shelf 3
map3.create_wall((425, 112), (82, 18))    # shelf 4 (above the right basin)
map3.create_wall((128, 284), (57, 41))    # stool
map3.create_wall((200, 214), (167, 111))  # counter, left of the sink
map3.create_wall((419, 214), (6, 111))    # divider between the two basins: the stepping stone
map3.create_wall((500, 214), (140, 111))  # counter, right of the sink
SINK_HOLES = [pygame.Rect(367, 230, 52, 95), pygame.Rect(425, 230, 75, 95)]   # fall in and you're stuck
map3.create_wall((566, 148), (74, 66))    # dish rack

map4 = Map("Hallway")
map4.create_wall((0, 320), (640, 40))     # floor
map4.create_wall((136, 298), (58, 22))    # toy car
map4.create_wall((268, 310), (38, 10))    # clothing
map4.create_wall((461, 260), (47, 60))    # middle box
map4.create_wall((506, 228), (125, 92))   # big box
map4.create_wall((553, 205), (29, 23))    # little box on top of the big box

map5 = Map("Bedroom")
# walk-only route: right along the floor, up the plank, over the pile, up to the right post,
# then back LEFT along the window sill, up the broken window plank, along the middle shelf,
# up the leaning pen onto the top shelf, to the teddy bear
map5.create_wall((0, 323), (640, 37))     # floor
map5.create_wall((0, 125), (208, 18))     # top-left shelf
map5.create_wall((9, 92), (34, 33))       # teddy bear
map5.create_slope((195, 323), (320, 210), step=4)  # leaning plank: floor up to the left bed post
map5.create_wall((320, 209), (32, 114))   # left bed post
map5.create_wall((354, 289), (90, 34))    # broken pile between the posts
map5.create_slope((480, 300), (589, 224), step=4)  # plank: pile up to the right bed post
map5.create_wall((589, 217), (48, 106))   # right bed post
map5.create_platform((479, 217), (110, 8))                # window sill (one-way)
map5.create_slope((369, 158), (479, 217), oneway=True)    # broken plank in the window: sill up to the middle shelf
map5.create_platform((187, 158), (182, 12))               # middle shelf (one-way)
map5.create_slope((208, 125), (238, 158))                 # leaning book: middle shelf up to the top-left shelf


FULL, DIM, CRITICAL = "full", "dim", "critical"
ROBOT = (34, 64)

# goalpos:  top-left corner of the star (32x32 pickup box, 24x24 sprite)
# exit:     "left" / "right": after the star, that screen edge opens and you walk out of the room;
#           "bear": the room ends when you reach the teddy bear
# loses:    ability that dies when the star is picked up: "run", "jump", "light" or None
# cutscene: picture shown after the room (None = black screen, the memory is gone)
LEVELS = [
    {
        "boxes": map1,
        "background": "background/Livingroom.png",
        "foreground": [],
        "start_pos": (66, 166),
        "car_size": ROBOT,
        "goalpos": (38, 20),              # above the left picture frame: table, desk, TV, shelf, frames
        "exit": "left",
        "abilities": {"jump": True, "run": True, "light": FULL},
        "loses": None,
        "enter": ["PIP-7 ... BOOT OK", "ALL SYSTEMS NOMINAL",
                  "TASK: COLLECT MIRI'S STARS.", "LOCATING MIRI... SEARCHING."],
        "pickup": ["STAR 1/5 STORED.", "EXIT: WEST."],
        "hint": ((30, 40, 110, 80), "PHOTO: MIRI AND PIP. DAY 212."),
        "cutscene": "background/cutscene_1.png",
    },
    {
        "boxes": map2,
        "background": "background/Study.png",
        "foreground": [],
        "start_pos": (66, 166),
        "car_size": ROBOT,
        "goalpos": (80, 14),              # on top of the bookcase: table, sprint jump to the shelves, bookcase
        "exit": "left",
        "abilities": {"jump": True, "run": True, "light": FULL},
        "loses": "run",
        "enter": ["ROOM: STUDY", "LOCATING MIRI... SEARCHING."],
        "pickup": ["STAR 2/5 STORED.", "DRIVE MOTOR: OFFLINE.", "EXIT: WEST."],
        "hint": ((470, 160, 120, 62), "DESK. A DRAWING: \"PIP\" IN CRAYON. DAY 212."),
        "cutscene": "background/cutscene_2.png",
    },
    {
        "boxes": map3,
        "background": "background/Kitchen.png",
        "foreground": [("foreground/drawers.png", (176, 205))],
        "start_pos": (66, 166),
        "car_size": ROBOT,
        "goalpos": (38, 28),              # on shelf 1 next to the vase: stool, counter, rack, shelves 4-3-2-1
        "exit": "left",
        "abilities": {"jump": True, "run": False, "light": FULL},
        "loses": "light",
        "enter": ["ROOM: KITCHEN", "LOCATING M~RI... SEARCHING."],
        "pickup": ["STAR 3/5 STORED.", "OPTICS: DEGRADED.", "EXIT: WEST."],
        "hint": ((100, 250, 100, 75), "HEIGHT MARKS: MIRI AGE 6. AGE 8. AGE 11. THEN NOTHING."),
        "cutscene": "background/cutscene_3.png",
    },
    {
        "boxes": map4,
        "background": "background/Hallway.png",
        "foreground": [("foreground/box.png", (419, 287))],
        "start_pos": (66, 166),
        "car_size": ROBOT,
        "goalpos": (552, 163),            # on the little box on top of the big box
        "exit": "right",                  # over the boxes, into the blocked door
        "abilities": {"jump": True, "run": False, "light": DIM},
        "loses": "light",
        "enter": ["ROOM: HALLWAY", "LOCATING ~~RI... SEARCHING."],
        "pickup": ["STAR 4/5 STORED.", "OPTICS: CRITICAL.", "EXIT: EAST."],
        "hint": ((120, 250, 90, 70), "TOY CAR. BATTERY: DEAD. LIKE MINE, SOON."),
        "cutscene": None,
    },
    {
        "boxes": map5,
        "background": "background/Bedroom.png",
        "foreground": [],
        "start_pos": (40, 250),
        "car_size": ROBOT,
        "goalpos": (112, 286),            # right by the door; the legs fail here, and the long walk begins
        "gated": False,                   # the star is not behind the ability; the whole room is the way back
        "exit": "bear",
        "bear": (9, 60, 40, 65),          # the teddy bear on the top shelf
        "abilities": {"jump": True, "run": False, "light": CRITICAL},
        "loses": "jump",
        "enter": ["ROOM: BEDROOM", "LOCATING ~~~~... SEARCHING."],
        "pickup": ["STAR 5/5 STORED.", "LEG ACTUATORS: OFFLINE.", "WALK ROUTE: AVAILABLE.", "~~~~ IS CLOSE."],
        "hint": ((330, 200, 300, 100), "BED. UNMADE SINCE DAY 4,312."),
        "cutscene": "background/cutscene_4.png",
    },
]

# The story. Everything is the robot's own log; it never understands what it is reading.
INTRO = ["PIP-7 HOUSEHOLD UNIT", "LAST SHUTDOWN: 4,312 DAYS AGO", "BATTERY: 11%",
         "TASK QUEUE: 1 ITEM", "> COLLECT MIRI'S STARS BEFORE BEDTIME.", "> RETURN TO MIRI.",
         "LOCATING MIRI... SEARCHING."]

MEMORIES = [
    ["MEMORY FRAGMENT 1 / 5 -- DAY 212", "\"Pip! Look, I drew you. You're the orange one.\"",
     "AUDIO: LAUGHTER (MIRI, AGE 6).", "FILED UNDER: GOOD DAYS."],
    ["MEMORY FRAGMENT 2 / 5 -- DAY 1,480", "MIRI READS ALOUD. PIP HOLDS THE PAGE.",
     "\"When I'm big I'll fix your motor myself.\"", "NOTE: MOTOR STILL UNFIXED."],
    ["MEMORY FRAGMENT 3 / 5 -- DAY 3,905", "FLOWERS ON THE KITCHEN SHELF. \"GET WELL\" ON THE CARD.",
     "MIRI SLEEPS A LOT NOW. PIP KEEPS THE WATER FRESH.", "AUDIO: COUGHING."],
    ["MEMORY FRAGMENT 4 / 5 -- DAY 4,3~~", "~~~~~~~~ ~~~~~ ~~~~~~~~~~~~ ~~~~",
     "AUDIO: A DOOR CLOSING.", "THEN NOTHING, FOR 4,312 DAYS."],
    None,
]

ENDING = ["STARS DELIVERED.", "TASK COMPLETE.", "LOCATING ~~~~..."]
ENDING_BEAR = ["THE BEAR IS WHERE SHE LEFT HIM.", "FIVE STARS. ALL OF THEM.", "BEDTIME. SHE SHOULD BE HERE."]
ENDING_MIRI = ["MEMORY FRAGMENT 5 / 5 -- DAY 4,312  (LAST RECORDED)",
               "\"Pip, stay with Bear. I'll be right back.\"",
               "AUDIO: AN AMBULANCE.", "SHE DID NOT COME BACK.", "LOCATING MIRI..."]
EXIT_WIDTH = 40           # how far past the edge the robot must walk to leave


def exit_zone(index):
    """Rectangle just outside the open edge; the robot overlaps it when it has left the room."""
    data = LEVELS[index]
    if data["exit"] == "left":
        return pygame.Rect(-EXIT_WIDTH, -1000, EXIT_WIDTH - ROBOT[0] + 4, 3000)
    if data["exit"] == "right":
        return pygame.Rect(ROOM_W + ROBOT[0] - 4, -1000, EXIT_WIDTH, 3000)
    return pygame.Rect(*data["bear"])
