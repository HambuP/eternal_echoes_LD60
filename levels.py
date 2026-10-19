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
# Falling below the sink bridge triggers a safe recall in Play.update.

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


# goalpos: top-left corner of the star
LEVELS = [
    {
        "boxes": map1,
        "background": "background/Livingroom.png",
        "foreground": None,
        "start_pos": (66, 166),
        "car_size": (34, 64),
        "goalpos": (38, 20),          # above the left picture frame
    },
    {
        "boxes": map2,
        "background": "background/Study.png",
        "foreground": None,
        "start_pos": (66, 166),
        "car_size": (34, 64),
        "goalpos": (80, 14),          # on top of the bookcase
    },
    {
        "boxes": map3,
        "background": "background/Kitchen.png",
        "foreground": None,           # later: the counter-front PNG drawn over the robot
        "start_pos": (66, 166),
        "car_size": (34, 64),
        "goalpos": (38, 28),          # on shelf 1, next to the vase
    },
    {
        "boxes": map4,
        "background": "background/Hallway.png",
        "foreground": None,           # later: the front box PNG
        "start_pos": (66, 166),
        "car_size": (34, 64),
        "goalpos": (552, 163),        # on the little box on top of the big box
    },
    {
        "boxes": map5,
        "background": "background/Bedroom.png",
        "foreground": None,
        "start_pos": (40, 250),
        "car_size": (34, 64),
        "goalpos": (50, 88),          # next to the teddy bear
    },
]

# Story entities use (x, feet-y) positions. All new traversal surfaces are drawn
# by the scene so the collision map never introduces invisible stepping stones.
ROOMS = [
    dict(title="THE PROMISE", objective="Wind the music box. Then follow the brass star.",
         device=(205, 305), device_name="Music box", required="drive", donate=False,
         checkpoint=(205, 241), memory=(387, 237),
         intro=("A promise in brass", "Pip wakes beneath a silent clock. In its hand: Miri's brass star. One task remains: bring the star to Bear before bedtime.", "Find the lamp on the floor and press E to pick it up. Press Esc, then H, for the full controls."),
         repaired_text="The music box remembers the tune. A tiny voice in the recording says: 'Bear can't sleep without his star.' Follow the glowing star to the next room.",
         memory_text="Miri's drawing: a crooked robot holding a sun. Underneath, in careful letters: PIP. 'You're not old,' she told it. 'You've just been here longer.'",
         extra=[], restored=[]),
    dict(title="A MAP OF HOME", objective="Scan the faded diagram at the desk terminal.",
         device=(531, 222), device_name="Desk terminal", required="lamp", donate=False,
         checkpoint=(490, 158), memory=(411, 74),
         intro=("Repairs, in her handwriting", "Miri's study is full of patient repairs. A faded diagram on the desk marks a route through the kitchen to her old bedroom.", "Disconnect the motor with 2, then connect the scanner with 3. Keep the springs for climbing."),
         repaired_text="Under the scanner, the route returns: Kitchen, hallway, then Bear. A folding step clicks into place. Miri left a way through.",
         memory_text="A letter, never posted: 'They offered me a new robot. But a new one wouldn't know where I hide the biscuits. I fixed Pip's motor instead.'",
         extra=[(365, 174, 64, 7)], restored=[(261, 104, 93, 7)]),
    dict(title="SOMETHING LEFT BEHIND", objective="Leave the motor at the pump to bridge the sink.",
         device=(94, 325), device_name="Sink pump", required="drive", donate=True,
         checkpoint=(62, 261), memory=(448, 192),
         intro=("One part can carry everyone", "The sink bridge is powerless. Pip's drive motor fits the empty pump housing. If it stays here, the bridge can hold for years.", "Connect the motor to repair the pump. You will keep walking and jumping, but lose sprinting. R always recalls you safely."),
         repaired_text="The motor settles into its new home. Water drains; the bridge unfolds. Pip's steps are slower now. Somewhere behind it, something old is useful again.",
         memory_text="A recipe card: 'Two biscuits for Miri. One pretend biscuit for Pip.' On the back: 'If a thing still helps someone, it isn't finished.'",
         extra=[], restored=[(365, 214, 139, 9)]),
    dict(title="A LIGHT TO FOLLOW", objective="Give the springs to the lift. Walk up its ramp.",
         device=(365, 320), device_name="Hall lift", required="jump", donate=True,
         checkpoint=(295, 230), memory=(300, 287),
         intro=("The house holds its breath", "The hall has gone dark. Bear's room is beyond the fallen boxes. The old lift needs a pair of springs; Pip has the last working pair.", "The scanner widens your light. Read the memory before leaving. Donating the springs creates a route you can walk."),
         repaired_text="The springs lift a long rescue ramp. Pip cannot jump now, but the house can carry it the rest of the way. Keep walking toward the light.",
         memory_text="A height mark on the wall: MIRI, AGE 8. Beneath it, a much lower line: PIP, AGE LOTS. 'There will always be room for you,' she said.",
         extra=[], restored=[]),
    dict(title="ONE LAST DELIVERY", objective="Reach Bear and connect the lamp to his night-light.",
         device=(76, 125), device_name="Bear's night-light", required="lamp", donate=False,
         checkpoint=(40, 259), memory=(293, 136),
         intro=("Before bedtime", "The bedroom is smaller than Pip remembers. The bed has fallen, but the planks still lead to the shelf. Bear is waiting where Miri left him.", "Walk right up the planks, then left along the window and shelves. The last working light is yours to share."),
         repaired_text="Pip sets the brass star beside Bear. The lamp warms the shelf. The promise is complete. For the first time all night, there is nowhere else Pip needs to be.",
         memory_text="A note tucked behind a book: 'Pip, if I'm away, please look after Bear. He pretends he isn't afraid of the dark. Love, Miri.'",
         extra=[], restored=[]),
]


def geometry(index, repaired=False):
    """Fresh collision lists; repairs never mutate shared level definitions."""
    base = LEVELS[index]["boxes"]
    walls = list(base.walls)
    platforms = list(base.platforms)
    new_platforms = [pygame.Rect(p) for p in ROOMS[index]["extra"]]
    if repaired:
        new_platforms += [pygame.Rect(p) for p in ROOMS[index]["restored"]]
    ramps = []
    if index == 3 and repaired:
        # Start well before the boxes and clear every solid on the ascent.
        ramps = [((314, 320), (553, 199))]
        walls += staircase(*ramps[0], step=4)
    if index == 4:
        # Bridge the original drop between bed posts: no jump module remains.
        ramps = [((354, 209), (440, 224))]
        platforms += staircase(*ramps[0], step=4)
        # The second plank joins the bridge at its upper end.
        ramps.append(((440, 224), (589, 217)))
        platforms += staircase(*ramps[1], step=4)
    platforms += new_platforms
    return walls, platforms, new_platforms, ramps
