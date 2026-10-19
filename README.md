# Old Tech: One Last Delivery

A short, five-room platform adventure about an aging household robot keeping a promise. Help Pip carry Miri's brass star to Bear, recover memories of their life together, and leave useful parts behind to bring the house back to life.

Built on the original LD60 **Old Tech** prototype, retaining its room artwork and robot animation sheets. The approved design and implementation plan is in [PLAN.md](PLAN.md).

## Quick start: install and play

You need **Python 3.11 or newer**, **Git** (for cloning), and a desktop display. Install Python from [python.org](https://www.python.org/downloads/) if it is missing. The game runs locally; no server, API key, or additional asset download is required.

Choose the commands for your operating system below. If you already cloned the repository, open a terminal in its folder and skip the first two lines. Keep that terminal open for the later commands.

### macOS / Linux

```sh
git clone --branch main https://github.com/HambuP/game.git
cd game
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python main.py
```

### Windows PowerShell

```powershell
git clone --branch main https://github.com/HambuP/game.git
cd game
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

These commands use the virtual environment directly, so you do **not** need to activate it or change PowerShell's execution policy. The dependency is `pygame-ce`, imported by the code as `pygame`; install the pinned package from `requirements.txt` rather than installing a separate `pygame` package.

**What you should see:** a window titled **Old Tech: One Last Delivery** with an **OLD TECH** title screen. Press **Enter** to start, then Enter or E to dismiss the opening story. Use Left / Right or A / D to move, Up / W / Space to jump, and E to interact.

### Play again later

Open a terminal in the repository folder and run just the launch command:

- macOS / Linux: `./.venv/bin/python main.py`
- Windows PowerShell: `.\.venv\Scripts\python.exe main.py`

Press **Enter** to continue your saved delivery. After finishing, Enter revisits the ending; **N** starts a new delivery. Replacing an existing save requires Enter to confirm, or Escape to cancel. Close the game window to exit.

The window is 1280 × 720 with a 640 × 360 game canvas. Assets load relative to the source, so an absolute path to `main.py` also works from another folder.

### If it does not start

- **Python command not found:** install Python 3.11 or newer, reopen your terminal, and retry. On Windows, use `python` instead of `py -3` for the environment-creation step if your installation does not include the `py` launcher.
- **`No module named pygame`:** repeat the dependency-install command above using the same `.venv` Python used to launch the game.
- **`main.py` or `requirements.txt` not found:** change into the repository folder; both files should be there.
- **Virtual environment creation fails on Linux:** install your distribution's Python `venv` support, then retry.
- **No game window:** launch from a desktop session. Headless/SSH sessions can run the automated checks below with a dummy display, but cannot show a playable window.

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
| J | Open the journal; toggle journal / pause menu |
| H while paused | Open / close the controls page |
| M | Mute / unmute music and robot sounds |
| Left / Right in journal | Browse the five room memories |
| Q while paused | Save and return to the menu |
| F1 | Toggle collision outlines for debugging |

You have **two sockets**. A third part cannot connect until you disconnect another. Parts can only be switched while grounded. A mint number badge in the bottom bar means connected, a dark badge means disconnected, and a dim label means the part is unavailable. Press Escape, then H, for the full controls. Each key has its own badge so instructions are easier to scan.

The scanner reveals mint diamond memory markers and expands your light in dark rooms. Read memories with E nearby. Memories are optional and change the ending text. Rooms close behind you, so collect a room's memory before following its exit star if you want all five.

There is no battery timer, combat, or limited stock of lives. **R** preserves repairs, parts, and memories. Falling into the kitchen basins recalls you automatically. Hold jump for the full arc when climbing high shelves.

## Audio

The game includes the seven original WAV files from your latest **Old House Robot** sound pack: mellow background jazz, walking footsteps, running thrusters, an idle motor, left/right servos, and jumping/landing effects. No separate download or audio package is required.

Music plays quietly from the title screen. Movement sounds follow the robot's actual actions; footsteps stop in midair or against a wall. The supplied jump recording is split for playback so takeoff and landing line up with the game. Robot sounds stop during pauses and story panels, while the music continues.

Press **M** anywhere to mute or unmute all audio for this session. The pause menu shows the sound status. If you hear nothing, check that it says **Sound on**, check your system output device/volume, and ensure the audio folder is present. A machine without an audio device can still run the game. Original file provenance and playback mapping are in [audio/README.md](audio/README.md).

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

From the repository folder, using the environment created above:

macOS / Linux:

```sh
./.venv/bin/python -m unittest discover -v
```

Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
```

Success prints `Ran 36 tests` and `OK`.

Tests use SDL's dummy display and audio drivers and temporary save files. They do not change your delivery save. The suite checks:

- Equipment limits, ownership, repair prerequisites, donations, and progression.
- Atomic save round trips, malformed data, unavailable storage, and safe new-game confirmation.
- Grounded module switching, coyote time, buffered jumps, variable jump height, sprinting, walls, and one-way platforms.
- Story/pause behavior, repeated pause/resume, memory collection, recalls, room transitions, ending interaction, and every scene's rendering.
- Launching from another working directory.
- Loading the original sound pack, movement-synchronized audio, mute/resume, pause silencing, original jump sample preservation, and graceful operation without an audio device.
- Instruction-panel bounds, spacing between keyboard badges, and controls/journal navigation.
- Recorded keyboard-input playthroughs through all five rooms, both with and without memory collection, without teleporting to objectives or bypassing collisions.
- Completing each room after continuing from a save made after its repair, including both permanent donations.

For a finite window/startup check on macOS / Linux:

```sh
./.venv/bin/python main.py --smoke 60
```

On Windows, run `.\.venv\Scripts\python.exe main.py --smoke 60`. The title screen opens briefly and exits automatically; omit `--smoke 60` to play.

For a headless smoke test on macOS / Linux:

```sh
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy ./.venv/bin/python main.py --smoke 5
```

A GitHub Actions workflow runs the suite and smoke test on Linux, macOS, and Windows with Python 3.11 and 3.14. See the repository's Actions tab for results on a particular commit.

## Manual playtest checklist

- Start a new delivery, cancel replacement of a save once, then confirm it.
- Verify both arrow and letter controls, short and full jumps, and motor-assisted sprinting.
- Try connecting a third part and switching in midair: both should show a clear explanation and preserve equipment.
- Read a memory without the scanner, then connect it and try again.
- Cancel each donation before confirming; the part should remain yours until confirmation.
- Recall in each room, fall into a sink basin, and continue after quitting immediately after each donation. Repairs must remain, and routes must still work.
- Pause and resume repeatedly, open the controls with H, browse journal pages, and check that the world remains still behind the overlay.
- Check jazz playback, walking versus thruster sounds, idle hum, directional servos, and jump/landing timing. Press M twice; all audio should mute, then resume. Pausing or opening a story must stop robot sounds.
- Complete the game with all five memories and once without collecting them. Both runs should finish, with different closing text.
- Check text, beacons, and the module bar at your display scale. The dark rooms should be navigable with the scanner.

Development verification: Python 3.14.7, pygame-ce 2.5.8, SDL 2.32.10 on macOS. The 36-test local suite, both full simulated playthroughs, all-room render checks, and native-window smoke test passed. Rendered screens were visually inspected. These checks reduce regression risk; they do not establish that every hardware/display combination is bug-free or replace human usability playtesting.

## Source layout

- `main.py`: fixed-step game loop and scene transitions.
- `scenes.py`: gameplay, interactions, story panels, HUD, journal, menu, and endings.
- `campaign.py`: campaign rules and validated save storage.
- `player.py`: movement, collisions, animation, and module-controlled abilities.
- `levels.py`: original room collision maps, story data, and repaired routes.
- `assets.py`: cached asset loading independent of the working directory.
- `ui.py`: typography, keyboard badges, spacing, and panel layouts.
- `sound.py` and `audio/`: synchronized playback and the original sound pack.
- `tests/`: rule, physics, scene, launch, and input-replay tests.

Original assets and code remain under the repository's [MIT license](LICENSE).
