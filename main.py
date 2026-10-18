import random
import pygame

GRID_SIZE = (16,9)
UNIT_SIZE = (64,64)

map = "################" \
      "................" \
      "####..##########" \
      "................" \
      "####..#######..#" \
      "................" \
      "................" \
      "...............#" \
      "################"

WIDTH, HEIGHT = GRID_SIZE[0]* UNIT_SIZE[0],GRID_SIZE[1]* UNIT_SIZE[1] #virtual screen
scale = 1 
FPS = 60

pygame.init() #start the pygames systems

screen = pygame.display.set_mode((WIDTH*scale,HEIGHT*scale)) #open a window with this dimensions
pygame.display.set_caption("Old Tech") #windows text title
canvas = pygame.Surface((WIDTH,HEIGHT))
clock = pygame.time.Clock() #use this to control fps

player = pygame.Rect(66,66*1,64,64)
speed = 3

running = True

def overlap(rect1,rect2):
    return pygame.Rect.colliderect(rect1,rect2)


class Map:
    def __init__(self,map):
        self.map = map
        self.walls= []

    def create_walls(self):
        for y in range(GRID_SIZE[1]):
            for x in range(GRID_SIZE[0]):
                if (map[y*GRID_SIZE[0]+ x] == "#"):
                    self.walls.append(pygame.Rect( x* UNIT_SIZE[0] , y* UNIT_SIZE[1] , UNIT_SIZE[0] , UNIT_SIZE[1] ))

map1 = Map(map)
map1.create_walls()

dx = 0
dy = 0
gravity= 0.3

onground = False
while running:


    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_UP and onground:
            dy = 7
            onground = False

    canvas.fill((30,30,40))

    keys = pygame.key.get_pressed()

    dx=0

    if keys[pygame.K_LEFT]:
        dx = -speed
    
    if keys[pygame.K_RIGHT]:
        dx = speed

    player.x += dx
    
    for wall in map1.walls:
        if overlap(wall,player):
            if dx > 0:
                player.right = wall.left
            if dx < 0:
                player.left = wall.right

    dy -= gravity
    player.y -= dy

    for wall in map1.walls:
        if overlap(wall,player):
            if dy > 0:
                player.top = wall.bottom
            if dy < 0:
                player.bottom = wall.top
                onground =True

            dy= 0
    

    if not keys[pygame.K_UP] and dy > 2:
        dy = 2

    if keys[pygame.K_DOWN]:
        speed = 4
    else:
        speed = 3

    for wall in map1.walls:
        pygame.draw.rect(canvas,(255,0,0),wall)

    pygame.draw.rect(canvas, (80,200,255),player)

    scaled = pygame.transform.scale(canvas, screen.get_size())
    screen.blit(scaled,(0,0))
    pygame.display.flip()

    clock.tick(60)

pygame.quit()


        