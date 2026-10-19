import pygame
import scenes

WIDTH, HEIGHT = 640, 360
SCALE = 2
FPS = 60

pygame.init()

screen = pygame.display.set_mode((WIDTH * SCALE, HEIGHT * SCALE))
pygame.display.set_caption("Old Tech")
canvas = pygame.Surface((WIDTH, HEIGHT))
clock = pygame.time.Clock()

scene = scenes.Menu()
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        else:
            scene.handle_event(event)

    scene.update()
    scene.draw(canvas)

    pygame.transform.scale(canvas, screen.get_size(), screen)
    pygame.display.flip()
    clock.tick(FPS)

    # switch screens if the current one asked to
    if scene.next_scene is not None:
        new_scene = scene.next_scene
        scene.next_scene = None
        scene = new_scene

pygame.quit()