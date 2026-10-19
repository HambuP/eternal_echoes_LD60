"""Campaign rules and persistence, independent of Pygame and its display."""
from dataclasses import dataclass, field
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODULES = ("jump", "drive", "lamp")
MODULE_NAMES = {"jump": "Jump springs", "drive": "Drive motor", "lamp": "Lamp / scanner"}


@dataclass
class Campaign:
    room: int = 0
    owned: set[str] = field(default_factory=lambda: {"jump", "drive"})
    equipped: list[str] = field(default_factory=lambda: ["jump", "drive"])
    repaired: set[int] = field(default_factory=set)
    memories: set[int] = field(default_factory=set)
    finished: bool = False

    def toggle(self, module):
        if module not in self.owned:
            return "Part unavailable. Find it or check the journal."
        if module in self.equipped:
            self.equipped.remove(module)
            return f"{MODULE_NAMES[module]} disconnected."
        if len(self.equipped) == 2:
            return "Both sockets are full. Switch one part off first."
        self.equipped.append(module)
        return f"{MODULE_NAMES[module]} connected."

    def salvage_lamp(self):
        self.owned.add("lamp")

    def repair(self, room):
        if type(room) is not int or room != self.room or not 0 <= room < 5:
            return False
        required = ("drive", "lamp", "drive", "jump", "lamp")[room]
        if room in self.repaired or (room == 0 and "lamp" not in self.owned):
            return False
        if required not in self.equipped:
            return False
        self.repaired.add(room)
        if room in (2, 3):
            self.equipped.remove(required)
            self.owned.remove(required)
        return True

    def advance(self):
        if self.finished or self.room not in self.repaired:
            return False
        if self.room == 4:
            self.finished = True
        else:
            self.room += 1
        return True

    def to_dict(self):
        return {"version": 1, "room": self.room, "owned": sorted(self.owned),
                "equipped": list(self.equipped), "repaired": sorted(self.repaired),
                "memories": sorted(self.memories), "finished": self.finished}

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict) or type(data.get("version")) is not int or data["version"] != 1:
            raise ValueError("Unsupported save")
        room = data.get("room")
        if type(room) is not int or not 0 <= room < 5:
            raise ValueError("Invalid room")
        def checked_list(key, allowed):
            value = data.get(key)
            if not isinstance(value, list) or len(value) > len(allowed):
                raise ValueError("Invalid " + key)
            if any(type(v) is not type(next(iter(allowed))) or v not in allowed for v in value):
                raise ValueError("Invalid " + key)
            if len(set(value)) != len(value):
                raise ValueError("Duplicate " + key)
            return value
        owned = set(checked_list("owned", MODULES))
        equipped = checked_list("equipped", MODULES)
        repaired = set(checked_list("repaired", range(5)))
        memories = set(checked_list("memories", range(5)))
        finished = data.get("finished")
        if type(finished) is not bool or len(equipped) > 2 or not set(equipped) <= owned:
            raise ValueError("Invalid equipment")
        if not set(range(room)) <= repaired or any(i > room for i in repaired | memories):
            raise ValueError("Invalid progression")
        if finished and (room != 4 or 4 not in repaired):
            raise ValueError("Invalid ending")
        expected = {"jump", "drive"}
        if "lamp" in owned:
            expected.add("lamp")
        if 2 in repaired:
            expected.discard("drive")
        if 3 in repaired:
            expected.discard("jump")
        if owned != expected or ((room > 0 or repaired or memories) and "lamp" not in owned):
            raise ValueError("Invalid parts")
        return cls(room, owned, equipped, repaired, memories, finished)


class SaveStore:
    def __init__(self, path=None):
        self.path = Path(path or os.environ.get("OLD_TECH_SAVE", ROOT / "saves" / "progress.json"))
        self.error = ""

    def load(self):
        self.error = ""
        try:
            return Campaign.from_dict(json.loads(self.path.read_text(encoding="utf-8")))
        except FileNotFoundError:
            return None
        except (OSError, ValueError, TypeError, UnicodeError):
            self.error = "Save unreadable. You can start a new delivery."
            return None

    def save(self, campaign):
        temporary = self.path.with_name(self.path.name + ".tmp")
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary.write_text(json.dumps(campaign.to_dict(), indent=2), encoding="utf-8")
            temporary.replace(self.path)
            self.error = ""
            return True
        except OSError:
            self.error = "Could not save. Your delivery can continue this session."
            return False
