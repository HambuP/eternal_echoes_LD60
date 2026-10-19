# Original robot sound pack

These seven unmodified WAV files are from the latest archive, **old_house_robot_sound_pack.zip**, in the user's **Robot Sound Effects** conversation (October 17, 2026). The matching downloaded files were supplied locally and selected by the user for this game. They replace no existing repository audio: none had previously been committed.

| File | Use |
| --- | --- |
| `dusty_house_jazz_loop.wav` | Quiet, repeating background jazz |
| `walk_two_legs.wav` | Walking loop while grounded and actually moving |
| `run_arm_thrusters.wav` | Thrusters while sprinting with the motor |
| `idle_worn_motor.wav` | Low idle hum while standing still |
| `turn_left.wav` | Left-turn servo |
| `turn_right.wav` | Right-turn servo |
| `jump_and_land.wav` | Takeoff and landing effects |

The jump recording includes both events. `sound.py` reads its takeoff at 0.10–1.15 seconds and landing at 1.28–1.85 seconds into separate playback buffers, preserving the original PCM samples. Actual jump and landing events trigger them, so short hops and long falls do not play a landing at the wrong time.

Music continues quietly through menus and story panels. Robot sounds stop when paused, reading, recalling, or changing rooms. **M** toggles all sound for the current session. The pause menu shows the sound status. If no audio device is available, the game remains playable and reports the condition.
