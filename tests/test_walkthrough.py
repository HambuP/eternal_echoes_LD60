"""Recorded input through all rooms; no position edits or fake collisions.

The fixture was found with a bounded search using Player.update, then replayed
through real Play handlers. Repairs/collection/equipment use keyboard events.
"""
import json
import tempfile
import unittest
from pathlib import Path
from tests.support import setup_display, keys, press
import pygame
from campaign import SaveStore
from scenes import Menu, Play, End

KEYS = {'right': pygame.K_RIGHT, 'left': pygame.K_LEFT,
        'up': pygame.K_UP, 'shift': pygame.K_LSHIFT}
ROUTE = json.loads(Path(__file__).with_name('walkthrough.json').read_text())


def dismiss(scene):
    while scene.dialog:
        press(scene, pygame.K_RETURN)


def settle(scene):
    for _ in range(100):
        if scene.robot.onground:
            return
        scene.update(keys())
    raise AssertionError('Robot never landed')


def equip(scene, modules):
    settle(scene)
    for module in list(scene.state.equipped):
        if module not in modules:
            press(scene, pygame.K_1 + ('jump', 'drive', 'lamp').index(module))
    for module in modules:
        if module not in scene.state.equipped:
            press(scene, pygame.K_1 + ('jump', 'drive', 'lamp').index(module))
    assert set(scene.state.equipped) == set(modules)


def replay(scene, step):
    for frames, held, jump in step['actions']:
        if jump:
            press(scene, pygame.K_UP)
        for _ in range(frames):
            scene.update(keys(*(KEYS[k] for k in held)))


def walk_campaign(store, collect_memories=True, snapshot=None):
    menu = Menu(store)
    press(menu, pygame.K_RETURN)
    scene = menu.next_scene
    for room in ROUTE:
        assert isinstance(scene, Play)
        assert scene.levelnum == room['room']
        dismiss(scene)
        if scene.levelnum == 1:
            equip(scene, ['jump', 'lamp'])
        elif scene.levelnum == 2:
            equip(scene, ['jump', 'drive'])
        for step in room['steps']:
            replay(scene, step)
            target = step['target']
            if target in ('salvage', 'device', 'memory'):
                if target != 'memory' or collect_memories:
                    kind, _ = scene.interaction()
                    assert kind == target, (scene.levelnum, target, kind, scene.robot.rect)
                    press(scene, pygame.K_e)
                    dismiss(scene)
                if target == 'device' and scene.levelnum in (0, 2):
                    equip(scene, ['jump', 'lamp'])
            elif target == 'exit':
                if scene.levelnum == 4:
                    press(scene, pygame.K_e)
                assert scene.collect_timer > 0, (scene.levelnum, scene.robot.rect)
            if snapshot:
                snapshot(scene, target)
        assert scene.levelnum in scene.state.repaired
        if collect_memories:
            assert scene.levelnum in scene.state.memories
        for _ in range(48):
            scene.update(keys())
        scene = scene.next_scene
    assert isinstance(scene, End)
    assert store.load().finished
    return scene


class WalkthroughTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        setup_display()

    def test_full_delivery_all_five_memories(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = SaveStore(Path(tmp) / 'save.json')
            ending = walk_campaign(store)
            self.assertEqual(ending.state.memories, set(range(5)))
            self.assertEqual(ending.state.owned, {'lamp'})

    def test_delivery_without_optional_memories(self):
        with tempfile.TemporaryDirectory() as tmp:
            ending = walk_campaign(SaveStore(Path(tmp) / 'save.json'), False)
            self.assertEqual(ending.state.memories, set())

    def test_continue_after_each_repair_remains_completable(self):
        from campaign import Campaign
        routes = json.loads(Path(__file__).with_name('resume_routes.json').read_text())
        state = Campaign()
        state.salvage_lamp()
        with tempfile.TemporaryDirectory() as tmp:
            store = SaveStore(Path(tmp) / 'save.json')
            for room, route in enumerate(routes):
                with self.subTest(room=room):
                    state.room = room
                    state.equipped = [('drive', 'lamp', 'drive', 'jump', 'lamp')[room]]
                    self.assertTrue(state.repair(room))
                    state.equipped = [p for p in ('jump', 'lamp') if p in state.owned]
                    self.assertTrue(store.save(state))
                    menu = Menu(store)
                    press(menu, pygame.K_RETURN)
                    scene = menu.next_scene
                    dismiss(scene)
                    replay(scene, route)
                    if room == 4:
                        press(scene, pygame.K_e)
                    self.assertGreater(scene.collect_timer, 0)
                    for _ in range(48):
                        scene.update(keys())
                    self.assertIsInstance(scene.next_scene, End if room == 4 else Play)
