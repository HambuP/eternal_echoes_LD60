import unittest
from tests.support import setup_display, press
import pygame
from ui import action_width, actions_row, panel_layout, prompt
from levels import ROOMS
from tests import test_game
from scenes import Pause


class LayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        setup_display()

    def test_all_story_content_clears_the_footer(self):
        for room in ROOMS:
            panels = [(room['intro'][1], room['intro'][2]),
                      (room['memory_text'], 'Saved in your journal. Press J to read it again. Memories are optional.'),
                      (room['repaired_text'], 'Press E beside Bear to finish the delivery.')]
            for body, note in panels:
                with self.subTest(body=body):
                    _, _, bottom = panel_layout(body, note)
                    self.assertLessEqual(bottom, 266)

    def test_action_badges_have_spacing_and_fit_the_card(self):
        surface = pygame.Surface((640, 360))
        for actions in ((("Enter", "Leave part"), ("Esc", "Keep part")),
                        (("Left / Right", "Browse"), ("J", "Back"), ("Esc", "Resume")),
                        (("Esc", "Resume"), ("Q", "Save and quit to menu"))):
            rects = actions_row(surface, actions, 291)
            self.assertGreaterEqual(rects[0].left, 64)
            self.assertLessEqual(rects[-1].right, 576)
            for left, right in zip(rects, rects[1:]):
                self.assertGreaterEqual(right.left - left.right, 24)
        for text in ('Springs', 'Motor', 'Scanner'):
            self.assertLess(action_width('1', text), 100)

    def test_context_prompts_stay_on_screen_at_both_edges(self):
        surface = pygame.Surface((640, 360))
        for x in (0, 320, 640):
            rect = prompt(surface, 'E', 'Scan desk terminal', x, 68)
            self.assertGreaterEqual(rect.left, 8)
            self.assertLessEqual(rect.right, 632)

    def test_controls_and_journal_have_separate_navigation(self):
        case = test_game.GameTests()
        case.setUp()
        self.addCleanup(case.temp.cleanup)
        play = case.play(2)
        pause = Pause(play)
        press(pause, pygame.K_h)
        self.assertTrue(pause.controls)
        self.assertFalse(pause.journal)
        press(pause, pygame.K_j)
        self.assertTrue(pause.journal)
        self.assertFalse(pause.controls)
        self.assertEqual(pause.page, 2)
        press(pause, pygame.K_RIGHT)
        self.assertEqual(pause.page, 3)
        press(pause, pygame.K_j)
        self.assertFalse(pause.journal)
        press(pause, pygame.K_h)
        press(pause, pygame.K_ESCAPE)
        self.assertIs(pause.next_scene, play)
