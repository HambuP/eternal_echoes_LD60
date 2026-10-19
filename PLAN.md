# Old Tech: One Last Delivery — implementation plan

## Approved direction
Combine the emotional delivery story (approach 1) with scavenged, interchangeable modules (approach 2). Keep the original five rooms, pixel art, and small Pygame application. Deliver a complete short adventure rather than add combat or a sprawling map.

## Story and progression
The household robot Pip wakes in a deserted home with a brass star and an old promise: bring it to Miri's bear before bedtime. The house is damaged, but memories reveal a loved companion rather than disposable machinery. Each restored device opens the next route. Leaving working parts behind makes the robot's declining abilities a visible, purposeful act.

1. **Living room / The promise:** teach movement, interaction, and sockets. Salvage the lamp beside the starting area. Use the drive motor to wind the music box; its tune establishes the delivery and activates the room beacon. An optional memory recalls Miri naming Pip.
2. **Study / A map of home:** equip the scanner to read a faded route diagram at a desk terminal. Two sockets force a choice among jumping, sprinting, and scanning. Restoring the terminal creates a helpful platform. An optional letter reveals that Miri kept repairing Pip.
3. **Kitchen / Something left behind:** dock the drive motor permanently to power a bridge over the sink. Explain the cost before confirmation. Add a recovery point and safe escape from the basins. The motor remains visibly active in the room; Pip continues with jump and scanner.
4. **Hallway / A light to follow:** use the scanner's wider light to navigate. Donate the jump springs to raise a ramp toward the exit, with an explicit confirmation and a walking route after the donation. Optional memory: Miri promised old things a place in her home.
5. **Bedroom / Delivery:** complete a walking ascent using the existing planks and shelves, adjusted wherever collision testing finds an obstruction. Return the brass star to the bear and power its night-light. The ending reflects recovered memories; the core delivery always succeeds without them.

## Mechanics and presentation
- Two power sockets, three modules: jump springs, sprint motor, lamp/scanner. Switch modules only while grounded; show installed/available/donated status and explain full sockets. Older character sprite sets fall back to compatible animations when a module enables an ability they originally lacked.
- Arrow keys or A/D move; Up/W/Space jump; Shift sprints with the motor; 1/2/3 toggle modules; E interacts; R recalls to the current recovery point; Esc pauses; J opens collected memories/help through the pause screen if appropriate.
- Contextual prompts, one clear room objective, brief skippable story panels, readable socket indicators, distinct repair stations and memory markers, soft darkness with glowing landmarks, and a satisfying delivery screen.
- Optional memory interaction requires the scanner. Memories affect ending text, never progression. No countdown or battery depletion.
- Add jump buffering and coyote time, retain variable jump height, and recover safely from falls and kitchen traps. Each donation must unlock geometry usable with the remaining modules.
- Save completed repairs, module ownership/equipment, memories, and current room. Continue resumes safely in that room; recalls preserve discoveries. Validate malformed saves and handle unavailable save storage without crashing.

## Implementation sequence
1. Record this plan, establish the Python/Pygame runtime, and preserve a clean branch baseline.
2. Separate campaign state and validated persistence from rendering. Add declarative room objectives, devices, story text, memories, and repair geometry.
3. Extend movement and asset loading for swappable modules, reliable recovery, and testable fixed-step simulation.
4. Build the campaign scenes, interactions, confirmations, module UI, journal, save/continue flow, and ending.
5. Verify every room with deterministic movement simulations using the actual collision code; repair any inaccessible objective or post-donation route.
6. Run regression tests for state/save validation, equipment restrictions, repairs, memory collection, recalls, scene transitions, movement, and all-room rendering. Inspect screenshots at native and enlarged size.
7. Write installation, controls, walkthrough, automated-test, and manual-playtest instructions. Record exact results and any remaining limitations.

## Acceptance criteria
- A new campaign can reach the ending through all five rooms using normal movement and interactions.
- Every mandatory device and exit is reachable, including after permanent donations and after loading a save.
- Optional memories are collectible without blocking the delivery or requiring a donated part later.
- Two-socket limits and module ownership are enforced; removing a module immediately removes its ability.
- Pause/dialogue freezes gameplay; recalls and room transitions do not corrupt persistent progress.
- All automated tests pass; launch/render smoke tests succeed; text fits the 640×360 canvas.
- README includes reproducible setup, test commands, all controls, a spoiler-marked solution, and a manual verification checklist.

## Scope and testing limits
Automated checks and a full simulated route substantially reduce defects but cannot prove that a game is bug-free on every computer. Report the tested Python/Pygame versions and distinguish automated checks from hands-on playtesting. Keep changes local on `codex/story-and-mechanics` unless publishing is requested.
