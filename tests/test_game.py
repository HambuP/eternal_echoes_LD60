import tempfile
import unittest
from pathlib import Path
from tests.support import setup_display, keys, press
import pygame
import levels
from campaign import Campaign, SaveStore
from player import Player
from scenes import Play, Pause, Menu, End, lines, font


class GameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        setup_display()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = SaveStore(Path(self.temp.name) / 'save.json')

    def play(self, room=0, repaired=False):
        state = Campaign(room=room, owned={'jump', 'drive', 'lamp'},
                         equipped=['jump', 'lamp'], repaired=set(range(room)))
        if room >= 3:
            state.owned.remove('drive')
        if room >= 4:
            state.owned.remove('jump')
            state.equipped = ['lamp']
        if repaired:
            state.equipped = [levels.ROOMS[room]['required']]
            state.repair(room)
        return Play(campaign=state, store=self.store, intro=False)

    def test_every_scene_renders(self):
        surface = pygame.Surface((640, 360))
        for room in range(5):
            for repaired in (False, True):
                scene = self.play(room, repaired)
                for _ in range(5):
                    scene.update(keys())
                scene.draw(surface)
                scene.debug = True
                scene.draw(surface)
                Pause(scene).draw(surface)
                Pause(scene, journal=True).draw(surface)
                scene.say(*scene.story['intro'][:2], note=scene.story['intro'][2])
                scene.draw(surface)
        Menu(self.store).draw(surface)
        End(store=self.store).draw(surface)

    def test_dialogue_and_pause_freeze_simulation(self):
        scene = self.play()
        scene.say('Wait', 'A memory')
        position = scene.robot.rect.copy()
        for _ in range(50):
            scene.update(keys(pygame.K_RIGHT))
        self.assertEqual(position, scene.robot.rect)
        press(scene, pygame.K_e)
        press(scene, pygame.K_ESCAPE)
        self.assertIsInstance(scene.next_scene, Pause)
        scene.update(keys(pygame.K_RIGHT))
        self.assertEqual(position, scene.robot.rect)

    def test_swap_ground_only_and_immediate_ability(self):
        scene = self.play()
        press(scene, pygame.K_1)
        self.assertTrue(scene.robot.can_jump)
        scene.robot.teleport((40, 241))
        scene.update(keys())
        self.assertTrue(scene.robot.onground)
        press(scene, pygame.K_1)
        self.assertFalse(scene.robot.can_jump)

    def test_lamp_required_before_first_room_unlock(self):
        scene = Play(store=self.store, intro=False)
        scene.robot.teleport((190, 241))
        scene.interact()
        self.assertNotIn(0, scene.state.repaired)
        scene.robot.teleport((95, 241))
        scene.interact()
        self.assertIn('lamp', scene.state.owned)

    def test_donation_confirmation_cancel_and_recall(self):
        scene = self.play(2)
        scene.state.equipped = ['jump', 'drive']
        scene.sync_modules()
        scene.robot.teleport((77, 261))
        scene.interact()
        self.assertIsNotNone(scene.dialog)
        press(scene, pygame.K_ESCAPE)
        self.assertIn('drive', scene.state.owned)
        scene.interact()
        press(scene, pygame.K_RETURN)
        self.assertNotIn('drive', scene.state.owned)
        self.assertIn(2, scene.state.repaired)
        scene.dialog = None
        scene.robot.teleport((380, 261))
        scene.update(keys())
        self.assertEqual(scene.robot.rect.topleft, scene.story['checkpoint'])
        self.assertIn(2, self.store.load().repaired)

    def test_memory_needs_scanner_and_persists(self):
        scene = self.play()
        mx, my = scene.story['memory']
        scene.robot.teleport((mx - 17, my - 54))
        scene.state.equipped = ['jump']
        scene.interact()
        self.assertEqual(scene.state.memories, set())
        scene.state.equipped.append('lamp')
        scene.interact()
        self.assertEqual(scene.state.memories, {0})
        self.assertEqual(self.store.load().memories, {0})
        scene.recall()
        self.assertEqual(scene.state.memories, {0})

    def test_exit_locked_until_repair_and_transition_saves(self):
        scene = self.play()
        scene.robot.teleport(scene.star.topleft)
        scene.update(keys())
        self.assertEqual(scene.collect_timer, 0)
        scene.state.repaired.add(0)
        scene.update(keys())
        self.assertGreater(scene.collect_timer, 0)
        for _ in range(48):
            scene.update(keys())
        self.assertIsInstance(scene.next_scene, Play)
        self.assertEqual(self.store.load().room, 1)

    def test_final_delivery_requires_interaction(self):
        scene = self.play(4, repaired=True)
        scene.robot.teleport((59, 61))
        scene.update(keys())
        self.assertEqual(scene.collect_timer, 0)
        scene.interact()
        for _ in range(48):
            scene.update(keys())
        self.assertIsInstance(scene.next_scene, End)
        self.assertTrue(self.store.load().finished)

    def test_geometry_does_not_mutate_between_campaigns(self):
        for room in range(5):
            before = levels.geometry(room, False)
            levels.geometry(room, True)
            self.assertEqual(before, levels.geometry(room, False))

    def test_story_panels_fit(self):
        for story in levels.ROOMS:
            bodies = [story['intro'][1], story['repaired_text'], story['memory_text']]
            for body in bodies:
                self.assertLessEqual(len(lines(body, 518, 21)), 5)
            body_height = len(lines(story['intro'][1], 518, 21)) * 24
            note_height = len(lines(story['intro'][2], 518, 18)) * 21
            self.assertLessEqual(116 + body_height + 12 + note_height, 278)


class PhysicsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        setup_display()

    def grounded(self):
        robot = Player((30, 236), (34, 64), 0)
        walls = [pygame.Rect(0, 300, 640, 60)]
        robot.update(keys(), walls, [])
        return robot, walls

    def test_variable_jump_and_no_jump_module(self):
        heights = []
        for held in (True, False):
            robot, walls = self.grounded()
            robot.jump_request = True
            top = robot.rect.y
            for _ in range(55):
                robot.update(keys(pygame.K_UP) if held else keys(), walls, [])
                top = min(top, robot.rect.y)
            heights.append(top)
            self.assertEqual(robot.rect.bottom, 300)
        self.assertLess(heights[0], heights[1] - 30)
        robot, walls = self.grounded()
        robot.can_jump = False
        robot.jump_request = True
        robot.update(keys(pygame.K_UP), walls, [])
        self.assertEqual(robot.rect.bottom, 300)

    def test_coyote_and_buffered_jump(self):
        robot, walls = self.grounded()
        robot.update(keys(), [], [])
        robot.jump_request = True
        robot.update(keys(pygame.K_UP), [], [])
        self.assertGreater(robot.dy, 0)
        robot.teleport((30, 230))
        robot.dy = -3
        robot.jump_request = True
        for _ in range(4):
            robot.update(keys(pygame.K_UP), walls, [])
        self.assertGreater(robot.dy, 0)

    def test_oneway_lands_from_above_and_passes_from_below(self):
        robot, walls = self.grounded()
        platform = pygame.Rect(0, 250, 200, 6)
        robot.jump_request = True
        reached_above = False
        for _ in range(60):
            robot.update(keys(pygame.K_UP), walls, [platform])
            reached_above |= robot.rect.bottom < 250
        self.assertTrue(reached_above)
        self.assertEqual(robot.rect.bottom, 250)

    def test_sprint_and_walls(self):
        robot, walls = self.grounded()
        robot.update(keys(pygame.K_RIGHT, pygame.K_LSHIFT), walls, [])
        self.assertEqual(robot.dx, 4)
        robot.can_run = False
        robot.update(keys(pygame.K_RIGHT, pygame.K_LSHIFT), walls, [])
        self.assertEqual(robot.dx, 3)
        walls.append(pygame.Rect(100, 200, 20, 100))
        for _ in range(30):
            robot.update(keys(pygame.K_RIGHT), walls, [])
        self.assertEqual(robot.rect.right, 100)
