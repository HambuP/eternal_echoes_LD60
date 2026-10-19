import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from tests.support import setup_display, keys, press
import pygame
from campaign import SaveStore
from main import take_transition
from scenes import Menu, Play, Pause


class RuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        setup_display()

    def test_launch_from_another_working_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            game = Path(__file__).resolve().parent.parent / 'main.py'
            env = dict(os.environ, OLD_TECH_SAVE=str(Path(tmp) / 'save.json'))
            result = subprocess.run([sys.executable, str(game), '--smoke', '3'],
                                    cwd=tmp, env=env, capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((Path(tmp) / 'save.json').exists())

    def test_repeated_pause_resume_does_not_reenter_old_pause(self):
        with tempfile.TemporaryDirectory() as tmp:
            scene = Play(store=SaveStore(Path(tmp) / 'save.json'), intro=False)
            for _ in range(3):
                original = scene
                press(scene, pygame.K_ESCAPE)
                scene = take_transition(scene)
                self.assertIsInstance(scene, Pause)
                press(scene, pygame.K_RETURN)
                scene = take_transition(scene)
                self.assertIs(scene, original)
                self.assertIsNone(scene.next_scene)
                before = scene.frames
                scene.update(keys())
                self.assertEqual(scene.frames, before + 1)

    def test_new_game_requires_confirmation_when_save_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = SaveStore(Path(tmp) / 'save.json')
            scene = Menu(store)
            press(scene, pygame.K_RETURN)
            state = scene.next_scene.state
            state.salvage_lamp()
            state.memories.add(0)
            store.save(state)
            menu = Menu(store)
            press(menu, pygame.K_n)
            self.assertIsNone(menu.next_scene)
            press(menu, pygame.K_ESCAPE)
            self.assertEqual(store.load().memories, {0})
            press(menu, pygame.K_n)
            press(menu, pygame.K_RETURN)
            self.assertIsInstance(menu.next_scene, Play)
            self.assertEqual(store.load().memories, set())
