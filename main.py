"""Run with `python main.py`; --smoke runs a finite, headless-friendly render check."""
import argparse
import pygame
import scenes

WIDTH, HEIGHT = 640, 360
SCALE = 2
FPS = 60


def take_transition(scene):
    """Clear the outgoing request, including scenes resumed after a pause."""
    if scene.next_scene is None:
        return scene
    next_scene = scene.next_scene
    scene.next_scene = None
    return next_scene


def main():
    parser = argparse.ArgumentParser(description="Old Tech: One Last Delivery")
    parser.add_argument("--smoke", type=int, default=0, metavar="FRAMES",
                        help="exit after this many rendered frames (does not start a campaign)")
    args = parser.parse_args()
    pygame.init()
    screen = pygame.display.set_mode((WIDTH * SCALE, HEIGHT * SCALE))
    pygame.display.set_caption("Old Tech: One Last Delivery")
    canvas = pygame.Surface((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    scene = scenes.Menu()
    running, frames, accumulator = True, 0, 0.0
    try:
        while running:
            accumulator += min(clock.tick(FPS) / 1000.0, 0.25)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    scene.handle_event(event)
            # Transitions take effect before another scene can simulate a frame.
            if scene.next_scene is not None:
                scene = take_transition(scene)
                accumulator = 0
            while accumulator >= 1 / FPS:
                scene.update()
                accumulator -= 1 / FPS
                if scene.next_scene is not None:
                    scene = take_transition(scene)
                    accumulator = 0
                    break
            scene.draw(canvas)
            pygame.transform.scale(canvas, screen.get_size(), screen)
            pygame.display.flip()
            frames += 1
            if args.smoke and frames >= args.smoke:
                running = False
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
