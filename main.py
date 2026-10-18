import random
import pygame

WIDTH, HEIGHT = 640, 360
scale = 2 
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
    def __init__(self,name):
        self.name = name
        self.walls= []

    def create_wall(self,point,size):
        self.walls.append(pygame.Rect(point[0],point[1],size[0],size[1]))
        

map1 = Map("Level 1")
map1.create_wall((0,200),(200,20))
map1.create_wall((440,200),(50,50))

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

    if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
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


        