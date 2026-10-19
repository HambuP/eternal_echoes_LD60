"""Echoes in the House. Run with `python main.py`; `--smoke N` renders N frames headlessly and exits."""
import argparse
import pygame
import scenes
import text
from sound import soundscape

SCALE = 3
FPS = 60


def switch(scene):
    nxt = scene.next_scene
    scene.next_scene = None
    soundscape.silence_robot()
    return nxt


def remap(event, canvas, screen):
    """Mouse events arrive in window pixels; scenes think in canvas pixels."""
    if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
        x, y = scenes.to_canvas(event.pos, canvas, screen)
        return pygame.event.Event(event.type, {**event.dict, "pos": (int(x), int(y))})
    return event


def main():
    parser = argparse.ArgumentParser(description="Echoes in the House")
    parser.add_argument("--smoke", type=int, default=0, metavar="FRAMES",
                        help="exit after this many rendered frames")
    parser.add_argument("--room", type=int, default=None, help="start directly in room 1-5")
    parser.add_argument("--plain-text", action="store_true",
                        help="draw text on the pixel canvas (lower resolution) if sharp text misbehaves")
    args = parser.parse_args()
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.init()
    soundscape.start()
    canvas = pygame.Surface((scenes.VIEW_W, scenes.VIEW_H))
    screen = pygame.display.set_mode((scenes.VIEW_W * SCALE, scenes.VIEW_H * SCALE))
    text.SCALE = 1 if args.plain_text else SCALE     # sharp text is rendered at window resolution, see text.label
    frame = pygame.Surface(screen.get_size())        # the frame is composed here, then copied to the window once
    pygame.display.set_caption("Echoes in the House")
    clock = pygame.time.Clock()
    scene = scenes.Play(args.room - 1) if args.room else scenes.Title()
    running, frames, accumulator = True, 0, 0.0
    try:
        while running:
            accumulator += min(clock.tick(FPS) / 1000.0, 0.25)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_m:
                    soundscape.toggle()
                elif event.type == pygame.WINDOWFOCUSLOST and isinstance(scene, scenes.Play):
                    scene.next_scene = scenes.Pause(scene)
                else:
                    scene.handle_event(remap(event, canvas, screen))
            if scene.next_scene is not None:
                scene = switch(scene)
                accumulator = 0
            while accumulator >= 1 / FPS:
                scene.update()
                accumulator -= 1 / FPS
                if scene.next_scene is not None:
                    scene = switch(scene)
                    accumulator = 0
                    break
            text.QUEUE.clear()
            text.FADE = 0
            scene.draw(canvas)
            pygame.transform.scale(canvas, frame.get_size(), frame)
            text.flush(frame)
            screen.blit(frame, (0, 0))
            pygame.display.flip()
            frames += 1
            if args.smoke and frames >= args.smoke:
                running = False
    finally:
        soundscape.close()
        pygame.quit()


if __name__ == "__main__":
    main()
