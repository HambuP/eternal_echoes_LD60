# Echoes in the House

*A short platformer about an old robot losing its parts, one room at a time.*
Made for Ludum Dare 60 (theme: **old tech**).

## The idea

You are PIP-7, an old household robot waking up in an empty house. Your last task:
collect Miri's stars and bring them to her. In each of five rooms there is one star,
hidden somewhere the close camera doesn't show you. Find it, and the way out opens.

But you are old tech. Every time you pick up a star, in the middle of the room,
one more system fails: your motor, then your optics, then your legs. The route you
came by no longer works, and you have to find the other way back with one ability
less. The house gets darker, and the last room you cross by walking only.

Nothing is on screen except the house, the robot, and the robot's own boot log.
The log is also the story: `LOCATING MIRI... SEARCHING.` degrades to `LOCATING ~~~~...`
as the rooms go by. The robot never finds out. You do, from the house.

## Controls

| | |
|---|---|
| Move | Arrows or A / D |
| Restart room | R |
| Jump | Up, W or Space (hold for higher) |
| Sprint | Shift, while the motor lasts |
| Pause | Esc |
| Music | M |
| Hitboxes | F1 (debug) |

## Rooms

| Room | You arrive with | The star costs you | Way out |
|---|---|---|---|
| Living room | everything | nothing yet (learn the loop: find the star, leave) | west edge |
| Study | sprint, jump | **drive motor**: no more sprint | west edge |
| Kitchen | jump | **optics**: the room goes dim | west edge |
| Hallway | jump, dim light | **optics**: a flickering circle of light | east, over the boxes |
| Bedroom | jump, almost no light | **leg actuators**, right at the door: the whole room is the walk back to Miri's bear | the bear |

Every star also wears the robot down a little: it walks and animates slower, the camera
lags more, and static builds up on its view. The screen edges are walls until the star
opens one of them; the boot log says which (`EXIT: WEST.`) and light spills in from it.
A sprint jump goes higher and further than a walking jump; that is the study's gate.
The kitchen sink has two holes: fall in and the only way out is R.

## Story

All of it is the robot's own log; PIP never understands what it is reading, the player does.
A boot sequence before room 1 (`LAST SHUTDOWN: 4,312 DAYS AGO`), one object per room that
logs a line when you pass it (the photo, the drawing, the height marks, the toy car, the bed),
and after each room a dated memory fragment with Miri's words over your friend's cutscene art.
The fourth fragment is corrupted. The ending: the bear, the last fragment, power-down.
Finishing a room unlocks the next on the room-select screen; progress is kept in `progress.json`.

## Play

```sh
git clone https://github.com/HambuP/game.git
cd game
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python main.py
```

On Windows PowerShell use `py -3 -m venv .venv` and `.\.venv\Scripts\python.exe` instead.
`python main.py --room 3` starts directly in a room; `--smoke 60` renders 60 frames and exits;
`--plain-text` draws the text on the pixel canvas instead of at window resolution, in case
sharp text misbehaves on your machine.

## Code

| File | What it does |
|---|---|
| `main.py` | the loop, canvas scaling (426x240 view, 3x window), scene switching |
| `scenes.py` | Title, Controls, RoomSelect, Play, Pause, LogScreen (intro / memories), End, PowerDown |
| `progress.py` | how many rooms are unlocked (progress.json) |
| `player.py` | physics (coyote time, jump buffer, variable jump height) and animation |
| `levels.py` | pure data: per room the collision boxes, art layers, star, door, abilities, boot log |
| `camera.py` | the close camera: lerp, look-ahead, clamp, shake |
| `text.py` | fonts, the boot log, button sprites |
| `sound.py` | the Old House Robot audio pack, synced to movement |
| `tools/routes.py` | route prover: searches the real physics to check every room's two routes |

### Designing a room

Each room in `levels.py` has a `goalpos` (star), an `exit` edge, a `hint` object, the
`abilities` you arrive with and the one the star `loses`. The story text is at the bottom of
the same file (`INTRO`, `MEMORIES`, `ENDING_*`). The rule: the star must need the ability that dies,
and the exit must be reachable without it (and at the slower speed), from wherever you
touched the star. Don't
trust your eyes on this; run

```sh
python tools/routes.py            # checks every room
python tools/routes.py 1 --map    # ASCII map of everything reachable in room 2
```

It presses every key combination against the actual `Player` physics, so if it says
a jump is sprint-only, it is.

## Credits

Room art, menu art, robot sprites and the audio pack by the team. Font: system monospace.
