"""The user's Old House Robot pack, synchronized with real movement events."""
from io import BytesIO
from pathlib import Path
import wave
import pygame

AUDIO_ROOT = Path(__file__).resolve().parent / "audio"
FILES = {
    "walk": "walk_two_legs.wav",
    "run": "run_arm_thrusters.wav",
    "idle": "idle_worn_motor.wav",
    "left": "turn_left.wav",
    "right": "turn_right.wav",
}
MUSIC = "dusty_house_jazz_loop.wav"
JUMP = "jump_and_land.wav"


def wav_slice(path, start, end):
    """Read an original recording segment; preserve its PCM samples and format."""
    with wave.open(str(path), "rb") as source:
        params = source.getparams()
        source.setpos(round(start * params.framerate))
        frames = source.readframes(round((end - start) * params.framerate))
    buffer = BytesIO()
    with wave.open(buffer, "wb") as target:
        target.setparams(params)
        target.writeframes(frames)
    buffer.seek(0)
    return buffer


class Soundscape:
    def __init__(self, root=AUDIO_ROOT):
        self.root = Path(root)
        self.ready = False
        self.muted = False
        self.error = ""
        self.motion = None
        self.sounds = {}
        self.channels = ()
        self.last_turn = -1000

    def start(self):
        if self.ready:
            return True
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            pygame.mixer.set_num_channels(8)
            pygame.mixer.set_reserved(3)
            self.channels = tuple(pygame.mixer.Channel(i) for i in range(3))
            self.sounds = {key: pygame.mixer.Sound(str(self.root / filename))
                           for key, filename in FILES.items()}
            # The supplied file has takeoff at 0.10–1.15 s and landing at
            # 1.28–1.85 s. Trigger each segment on its physical event instead
            # of playing a landing at a fixed delay during a short hop.
            self.sounds["jump"] = pygame.mixer.Sound(file=wav_slice(self.root / JUMP, 0.10, 1.15))
            self.sounds["land"] = pygame.mixer.Sound(file=wav_slice(self.root / JUMP, 1.28, 1.85))
            for key, sample in self.sounds.items():
                sample.set_volume(0.12 if key == "idle" else 0.32 if key in ("walk", "run") else 0.42)
            pygame.mixer.music.load(str(self.root / MUSIC))
            pygame.mixer.music.set_volume(0.28)
            pygame.mixer.music.play(-1, fade_ms=600)
            self.ready = True
            self.error = ""
            if self.muted:
                pygame.mixer.music.pause()
            return True
        except (pygame.error, OSError, EOFError, wave.Error) as error:
            self.error = f"Audio unavailable: {error}"
            self.ready = False
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
                for channel in self.channels:
                    channel.stop()
            return False

    def silence_robot(self):
        if self.ready:
            for channel in self.channels:
                channel.stop()
        self.motion = None

    def set_motion(self, mode):
        if mode == self.motion:
            return
        self.motion = mode
        channel = self.channels[0]
        channel.stop()
        if mode:
            channel.play(self.sounds[mode], loops=-1, fade_ms=80)

    def update_robot(self, robot, *, moving, jumped=False, landed=False, turned=False):
        if not self.ready or self.muted:
            return
        mode = None
        if robot.onground and not robot.collecting:
            mode = "run" if moving and abs(robot.dx) > 3 else "walk" if moving else "idle"
        self.set_motion(mode)
        if jumped:
            self.channels[2].play(self.sounds["jump"], fade_ms=8)
        elif landed:
            self.channels[2].play(self.sounds["land"], fade_ms=8)
        now = pygame.time.get_ticks()
        if turned and now - self.last_turn >= 180:
            self.last_turn = now
            self.channels[1].play(self.sounds["right" if robot.right else "left"], fade_ms=20)

    def toggle(self):
        self.muted = not self.muted
        self.silence_robot()
        if self.ready:
            if self.muted:
                pygame.mixer.music.pause()
            else:
                pygame.mixer.music.unpause()
        return self.muted

    @property
    def status(self):
        if not self.ready:
            return "Audio unavailable" if self.error else "Sound off"
        return "Sound off" if self.muted else "Sound on"

    def close(self):
        self.silence_robot()
        if self.ready:
            pygame.mixer.music.stop()
        self.ready = False


soundscape = Soundscape()
