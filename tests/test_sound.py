from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import tempfile
import unittest
import wave
from tests.support import setup_display, keys, press
import pygame
from campaign import SaveStore
from scenes import Play, Pause
from sound import Soundscape, AUDIO_ROOT, JUMP, wav_slice
from tests.test_walkthrough import walk_campaign


class SoundTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        setup_display()

    def setUp(self):
        self.audio = Soundscape()
        self.addCleanup(self.audio.close)
        self.assertTrue(self.audio.start(), self.audio.error)
        self.robot = SimpleNamespace(onground=True, collecting=False, dx=0, right=True)

    def test_pack_loads_and_background_music_plays(self):
        self.assertTrue(pygame.mixer.music.get_busy())
        self.assertEqual(set(self.audio.sounds), {'walk', 'run', 'idle', 'left', 'right', 'jump', 'land'})
        self.assertTrue(all(sound.get_length() > 0 for sound in self.audio.sounds.values()))

    def test_movement_loops_follow_motion_and_stop_in_air(self):
        self.audio.update_robot(self.robot, moving=False)
        self.assertEqual(self.audio.channels[0].get_sound(), self.audio.sounds['idle'])
        self.robot.dx = 3
        self.audio.update_robot(self.robot, moving=True)
        self.assertEqual(self.audio.channels[0].get_sound(), self.audio.sounds['walk'])
        self.robot.dx = 4
        self.audio.update_robot(self.robot, moving=True)
        self.assertEqual(self.audio.channels[0].get_sound(), self.audio.sounds['run'])
        # Pressing into a wall is not movement, even with sprint held.
        self.audio.update_robot(self.robot, moving=False)
        self.assertEqual(self.audio.motion, 'idle')
        self.robot.onground = False
        self.audio.update_robot(self.robot, moving=True)
        self.assertIsNone(self.audio.channels[0].get_sound())

    def test_jump_landing_and_turning_use_separate_channels(self):
        self.robot.onground = False
        self.robot.right = False
        self.audio.update_robot(self.robot, moving=True, jumped=True, turned=True)
        self.assertEqual(self.audio.channels[1].get_sound(), self.audio.sounds['left'])
        self.assertEqual(self.audio.channels[2].get_sound(), self.audio.sounds['jump'])
        self.robot.onground = True
        self.audio.update_robot(self.robot, moving=False, landed=True)
        self.assertEqual(self.audio.channels[2].get_sound(), self.audio.sounds['land'])

    def test_mute_stops_effects_and_resumes_music(self):
        self.audio.update_robot(self.robot, moving=False)
        self.assertTrue(self.audio.toggle())
        self.assertFalse(pygame.mixer.music.get_busy())
        self.assertTrue(all(not channel.get_busy() for channel in self.audio.channels))
        self.audio.update_robot(self.robot, moving=True, jumped=True)
        self.assertTrue(all(not channel.get_busy() for channel in self.audio.channels))
        self.assertFalse(self.audio.toggle())
        self.assertTrue(pygame.mixer.music.get_busy())
        self.audio.update_robot(self.robot, moving=False)
        self.assertTrue(self.audio.channels[0].get_busy())

    def test_missing_assets_and_missing_device_are_nonfatal(self):
        self.audio.close()
        with tempfile.TemporaryDirectory() as tmp:
            missing = Soundscape(tmp)
            self.assertFalse(missing.start())
            self.assertTrue(missing.error)
            missing.update_robot(self.robot, moving=True, jumped=True)
        with patch('pygame.mixer.get_init', return_value=None), patch('pygame.mixer.init', side_effect=pygame.error('No device')):
            unavailable = Soundscape()
            self.assertFalse(unavailable.start())
            self.assertIn('No device', unavailable.error)

    def test_jump_segments_preserve_original_pcm(self):
        with wave.open(str(AUDIO_ROOT / JUMP)) as source:
            source.setpos(round(1.28 * source.getframerate()))
            expected = source.readframes(round((1.85 - 1.28) * source.getframerate()))
        with wave.open(wav_slice(AUDIO_ROOT / JUMP, 1.28, 1.85)) as clipped:
            self.assertEqual(clipped.readframes(clipped.getnframes()), expected)

    def test_full_campaign_with_sound_and_pause_silencing(self):
        with tempfile.TemporaryDirectory() as tmp, patch('scenes.soundscape', self.audio):
            store = SaveStore(Path(tmp) / 'save.json')
            scene = Play(store=store, intro=False)
            for _ in range(30):
                scene.update(keys())
            self.assertEqual(self.audio.motion, 'idle')
            press(scene, pygame.K_ESCAPE)
            self.assertIsInstance(scene.next_scene, Pause)
            self.assertTrue(all(not channel.get_busy() for channel in self.audio.channels))
            scene.next_scene = None
            scene.say('A memory', 'The robot waits.')
            for _ in range(5):
                scene.update(keys(pygame.K_RIGHT))
            self.assertIsNone(self.audio.motion)
            ending = walk_campaign(store)
            self.assertTrue(ending.state.finished)
