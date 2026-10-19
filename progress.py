
import json
from assets import ROOT

PATH = ROOT / "progress.json"
TOTAL = 5


def load():
    try:
        return max(1, min(TOTAL, int(json.loads(PATH.read_text())["unlocked"])))
    except (OSError, ValueError, KeyError, TypeError):
        return 1


def unlock(count):
    count = max(load(), min(TOTAL, count))
    try:
        PATH.write_text(json.dumps({"unlocked": count}))
    except OSError:
        pass
    return count
