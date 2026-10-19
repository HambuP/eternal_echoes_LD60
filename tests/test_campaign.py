import json
import tempfile
import unittest
from pathlib import Path
from campaign import Campaign, SaveStore


class CampaignTests(unittest.TestCase):
    def test_slots_and_ownership(self):
        state = Campaign()
        state.toggle('lamp')
        self.assertNotIn('lamp', state.equipped)
        state.salvage_lamp()
        state.toggle('lamp')
        self.assertEqual(len(state.equipped), 2)
        state.toggle('drive')
        state.toggle('lamp')
        self.assertEqual(state.equipped, ['jump', 'lamp'])

    def test_repairs_donations_and_final_delivery(self):
        state = Campaign()
        self.assertFalse(state.advance())
        state.salvage_lamp()
        for room, required in enumerate(('drive', 'lamp', 'drive', 'jump', 'lamp')):
            self.assertEqual(state.room, room)
            state.equipped = [required]
            self.assertTrue(state.repair(room))
            self.assertFalse(state.repair(room))
            if room in (2, 3):
                self.assertNotIn(required, state.owned)
                self.assertNotIn(required, state.equipped)
            self.assertTrue(state.advance())
            self.assertEqual(Campaign.from_dict(state.to_dict()).to_dict(), state.to_dict())
        self.assertTrue(state.finished)
        self.assertEqual(state.owned, {'lamp'})

    def test_wrong_module_cannot_repair(self):
        state = Campaign(equipped=['jump'])
        self.assertFalse(state.repair(0))
        self.assertEqual(state.repaired, set())

    def test_atomic_save_roundtrip_and_corrupt_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'nested' / 'save.json'
            store = SaveStore(path)
            self.assertIsNone(store.load())
            self.assertEqual(store.error, '')
            state = Campaign()
            self.assertTrue(store.save(state))
            self.assertEqual(store.load(), state)
            self.assertFalse(path.with_name('save.json.tmp').exists())
            for bad in ('{', 'null', '[]', '{"version":999}', '\udcff'):
                path.write_bytes(bad.encode('utf-8', errors='surrogatepass'))
                self.assertIsNone(store.load())
                self.assertTrue(store.error)
            path.write_text(json.dumps(state.to_dict()))
            self.assertEqual(store.load(), state)
            self.assertEqual(store.error, '')

    def test_reject_invalid_progress_and_equipment(self):
        base = Campaign().to_dict()
        for key, value in [('room', True), ('room', -1), ('room', 5), ('room', 2),
                           ('owned', ['jump', 'warp']), ('equipped', ['lamp']),
                           ('equipped', ['jump', 'jump']), ('memories', [True]),
                           ('repaired', [2]), ('finished', True), ('finished', 1),
                           ('owned', [{}]), ('memories', 'zero')]:
            with self.subTest(key=key, value=value):
                with self.assertRaises(ValueError):
                    Campaign.from_dict(dict(base, **{key: value}))

    def test_unwritable_save_is_nonfatal(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'file'
            path.write_text('occupied')
            store = SaveStore(path / 'save.json')
            self.assertFalse(store.save(Campaign()))
            self.assertTrue(store.error)
