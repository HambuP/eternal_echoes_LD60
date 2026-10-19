import math
import pygame


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
map2.create_wall((365, 96), (111, 17))    # upper shelf
map2.create_wall((469, 120), (111, 18))   # lower shelf
map2.create_wall((290, 302), (101, 18))   # wood pile, base
map2.create_wall((320, 281), (50, 21))    # wood pile, peak
map2.create_wall((406, 222), (234, 24))   # table top
map2.create_wall((418, 246), (20, 74))    # table front leg
map2.create_wall((567, 215), (55, 7))     # flat book on table
map2.create_wall((621, 169), (19, 53))    # standing book on table

map3 = Map("Kitchen")
map3.create_wall((0, 325), (640, 35))     # floor
map3.create_wall((0, 74), (74, 18))       # shelf 1
map3.create_wall((2, 38), (28, 36))       # vase on shelf 1
map3.create_wall((135, 73), (83, 18))     # shelf 2
map3.create_wall((286, 73), (81, 18))     # shelf 3
map3.create_wall((425, 112), (82, 18))    # shelf 4 (above the right basin)
map3.create_wall((128, 284), (57, 41))    # stool
map3.create_wall((200, 214), (167, 111))  # counter, left of the sink
map3.create_wall((419, 214), (6, 111))    # divider between the two basins
map3.create_wall((500, 214), (140, 111))  # counter, right of the sink (edge moved left so the jump under shelf 4 is possible)
map3.create_wall((566, 148), (74, 66))    # dish rack
# the basins have no bottom: fall in and you land on the floor, too deep to jump out

map4 = Map("Hallway")
map4.create_wall((0, 320), (640, 40))     # floor
map4.create_wall((136, 298), (58, 22))    # toy car
map4.create_wall((268, 310), (38, 10))    # clothing
map4.create_wall((461, 260), (47, 60))    # middle box
map4.create_wall((506, 228), (125, 92))   # big box
map4.create_wall((553, 205), (29, 23))    # little box on top of the big box

map5 = Map("Bedroom")
# route: right along the floor, up the plank, over the pile, up to the right post,
# then back LEFT along the window sill, up the broken window plank, along the middle shelf,
# up the leaning pen onto the top shelf, to the teddy bear
map5.create_wall((0, 323), (640, 37))     # floor
map5.create_wall((0, 125), (208, 18))     # top-left shelf
map5.create_wall((9, 92), (34, 33))       # teddy bear
map5.create_slope((164, 323), (312, 216), step=4)  # leaning plank: floor up to the left bed post
map5.create_wall((312, 209), (42, 114))   # left bed post
map5.create_wall((354, 289), (70, 34))    # broken pile between the posts
map5.create_slope((440, 289), (589, 224), step=4)  # plank: pile up to the right bed post
map5.create_wall((589, 217), (48, 106))   # right bed post
map5.create_platform((479, 217), (110, 8))                # window sill (one-way)
map5.create_slope((369, 158), (479, 217), oneway=True)    # broken plank in the window: sill up to the middle shelf
map5.create_platform((187, 158), (182, 12))               # middle shelf (one-way)
map5.create_slope((208, 125), (238, 158))                 # leaning pen: middle shelf up to the top-left shelf


# visibility: None = see everything, a number = radius of the light circle around the robot
# goalpos: top-left corner of the star
LEVELS = [
    {
        "boxes": map1,
        "background": "background/Livingroom.png",
        "foreground": None,
        "start_pos": (66, 166),
        "car_size": (34, 64),
        "goalpos": (38, 20),          # above the left picture frame
        "run": True,
        "jump": True,
        "visibility": None,
    },
    {
        "boxes": map2,
        "background": "background/Study.png",
        "foreground": None,
        "start_pos": (66, 166),
        "car_size": (34, 64),
        "goalpos": (80, 14),          # on top of the bookcase
        "run": True,
        "jump": True,
        "visibility": None,
    },
    {
        "boxes": map3,
        "background": "background/Kitchen.png",
        "foreground": None,           # later: the counter-front PNG drawn over the robot
        "start_pos": (66, 166),
        "car_size": (34, 64),
        "goalpos": (38, 28),          # on shelf 1, next to the vase
        "run": False,
        "jump": True,
        "visibility": None,
    },
    {
        "boxes": map4,
        "background": "background/Hallway.png",
        "foreground": None,           # later: the front box PNG
        "start_pos": (66, 166),
        "car_size": (34, 64),
        "goalpos": (552, 163),        # on the little box on top of the big box
        "run": False,
        "jump": True,
        "visibility": 90,
    },
    {
        "boxes": map5,
        "background": "background/Bedroom.png",
        "foreground": None,
        "start_pos": (40, 250),
        "car_size": (34, 64),
        "goalpos": (50, 88),          # next to the teddy bear
        "run": False,
        "jump": False,
        "visibility": 90,
    },
]