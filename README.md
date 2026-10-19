# Old Tech: One Last Delivery

A short, five-room platform adventure about an aging household robot keeping a promise. Help Pip carry Miri's brass star to Bear, recover memories of their life together, and leave useful parts behind to bring the house back to life.

Built on the original LD60 **Old Tech** prototype, retaining its room artwork and robot animation sheets. The approved design and implementation plan is in [PLAN.md](PLAN.md).

## Install and play

Requires **Python 3.11 or newer** and a desktop display. The game uses `pygame-ce` (imported as `pygame`); no other game framework or asset download is needed. Use a virtual environment to avoid conflicts with a separate `pygame` installation.

### macOS / Linux

From the repository folder:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

### Windows PowerShell

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

The window is 1280 × 720 with a 640 × 360 game canvas. Assets load relative to the source, so an absolute path to `main.py` also works from another folder.

Press **Enter** to begin or continue. After finishing, Enter revisits the ending; **N** starts a new delivery. Replacing an existing save requires Enter to confirm, or Escape to cancel.

## Controls

| Key | Action |
| --- | --- |
| Left / Right or A / D | Move |
| Up / W / Space | Jump with connected springs; release early for a short hop |
| Shift + move | Sprint with the connected motor |
| 1 | Connect / disconnect jump springs |
| 2 | Connect / disconnect drive motor |
| 3 | Connect / disconnect lamp / scanner |
| E | Salvage, use a device, read a memory, or complete the delivery |
| Enter / E | Dismiss a story panel |
| Enter / Escape | Confirm / cancel a permanent part donation |
| R | Recall to the room's safe starting point or recovery point |
| Escape | Pause / resume; dismiss a normal story panel |
| J | Open the journal; toggle journal / controls while paused |
| Left / Right in journal | Browse the five room memories |
| Q while paused | Save and return to the menu |
| F1 | Toggle collision outlines for debugging |

You have **two sockets**. A third part cannot connect until you disconnect another. Parts can only be switched while grounded. A filled mint square in the bottom bar means connected, an outline means available, and a dim label means unavailable.

The scanner reveals mint diamond memory markers and expands your light in dark rooms. Read memories with E nearby. Memories are optional and change the ending text. Rooms close behind you, so collect a room's memory before following its exit star if you want all five.

There is no battery timer, combat, or limited stock of lives. **R** preserves repairs, parts, and memories. Falling into the kitchen basins recalls you automatically. Hold jump for the full arc when climbing high shelves.

## Saves

Repairs, parts, equipment, memories, and room transitions save automatically to `saves/progress.json`, ignored by Git. Continue restores a safe position in the current room; it does not restore your exact mid-jump position. Donations are permanent for that delivery. A new game resets them.

To keep separate profiles or use a writable location when the repository is read-only, set `OLD_TECH_SAVE` to another file path before launching. A corrupt save returns you to the menu with a message. Save-storage failures show an in-game notice and let you keep playing in the current session.

## Walkthrough — spoilers

1. **Living room:** land on the floor and press E near the small lamp to salvage it. Keep the motor connected and use the music box farther right. For the optional memory, disconnect the motor with 2 and connect the scanner with 3, keeping the springs. Jump onto the small round table and read its memory. Climb from the table to the desk / TV, then back left across the wall shelf and picture frames to the star.
2. **Study:** use springs + scanner. Climb the wood pile to the desk and scan the terminal. It unfolds a new step. Use the visible mint-edged step and wall shelves to reach the upper-right memory, then work left across the restored step to the bookcase star.
3. **Kitchen:** connect the motor before using the pump near the starting area; disconnect the scanner temporarily if both sockets are full. Confirm with Enter to leave the motor and raise the sink bridge. Reconnect the scanner, keeping the springs. Jump from the stool to the counter, read the memory on the sink bridge, then climb the dish rack and cross the upper shelves back left to the star. If you fall below the sink, recall keeps the bridge repaired.
4. **Hallway:** keep springs + scanner. Walk right and jump over the toy car. Read the optional memory by the clothing before reaching the lift. Use the lift and confirm the spring donation; a ramp appears over the boxes. Walk right up the ramp to the star. You no longer need to jump.
5. **Bedroom:** keep the scanner connected. Walk right up the leaning plank, cross the restored bridges to the right bedpost, then walk left along the window sill and broken plank to the middle shelf. Read the memory, climb the leaning pen to the upper-left shelf, and reach Bear. Use the night-light with E, dismiss the story, then press E again to deliver the star. All five memories reveal the fuller ending.

## Automated tests

With the virtual environment active:

```sh
python -m unittest discover -v
```

Tests use SDL's dummy display and audio drivers and temporary save files. They do not change your delivery save. The suite checks:

- Equipment limits, ownership, repair prerequisites, donations, and progression.
- Atomic save round trips, malformed data, unavailable storage, and safe new-game confirmation.
- Grounded module switching, coyote time, buffered jumps, variable jump height, sprinting, walls, and one-way platforms.
- Story/pause behavior, repeated pause/resume, memory collection, recalls, room transitions, ending interaction, and every scene's rendering.
- Launching from another working directory.
- Recorded keyboard-input playthroughs through all five rooms, both with and without memory collection, without teleporting to objectives or bypassing collisions.
- Completing each room after continuing from a save made after its repair, including both permanent donations.

For a finite render/startup smoke test:

```sh
python main.py --smoke 60
```

For a headless smoke test on macOS / Linux:

```sh
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python main.py --smoke 5
```

A GitHub Actions workflow runs the suite and smoke test on Linux, macOS, and Windows with Python 3.11 and 3.14. See the repository's Actions tab for results on a particular commit.

## Manual playtest checklist

- Start a new delivery, cancel replacement of a save once, then confirm it.
- Verify both arrow and letter controls, short and full jumps, and motor-assisted sprinting.
- Try connecting a third part and switching in midair: both should show a clear explanation and preserve equipment.
- Read a memory without the scanner, then connect it and try again.
- Cancel each donation before confirming; the part should remain yours until confirmation.
- Recall in each room, fall into a sink basin, and continue after quitting immediately after each donation. Repairs must remain, and routes must still work.
- Pause and resume repeatedly, browse journal pages, and check that the world remains still behind the overlay.
- Complete the game with all five memories and once without collecting them. Both runs should finish, with different closing text.
- Check text, beacons, and the module bar at your display scale. The dark rooms should be navigable with the scanner.

Development verification: Python 3.14.7, pygame-ce 2.5.8, SDL 2.32.10 on macOS. The 26-test local suite, both full simulated playthroughs, all-room render checks, and native-window smoke test passed. Rendered screens were visually inspected. These checks reduce regression risk; they do not establish that every hardware/display combination is bug-free or replace human usability playtesting.

## Source layout

- `main.py`: fixed-step game loop and scene transitions.
- `scenes.py`: gameplay, interactions, story panels, HUD, journal, menu, and endings.
- `campaign.py`: campaign rules and validated save storage.
- `player.py`: movement, collisions, animation, and module-controlled abilities.
- `levels.py`: original room collision maps, story data, and repaired routes.
- `assets.py`: cached asset loading independent of the working directory.
- `tests/`: rule, physics, scene, launch, and input-replay tests.

Original assets and code remain under the repository's [MIT license](LICENSE).
