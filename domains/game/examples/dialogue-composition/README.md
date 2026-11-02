# Native branching dialogue composition — Godot + upstream Dialogue Manager

This is a **runnable Game LEGO consumer**, not a shipped game or a second narrative language. The exact upstream Godot addon is owned by its maintainers; this example owns the gate state, choice UI and game-specific contract.

- Engine: `Godot 4.7.2`, as pinned by `domains/game/mise.toml`.
- Upstream: [nathanhoad/godot_dialogue_manager](https://github.com/nathanhoad/godot_dialogue_manager/releases/tag/v4.2.0), version **4.2.0** (GitHub Latest on 2026-11-02), exact commit **`bbf9d2a5f6a9eaa276310eea8b1379a936239d2e`**.
- License: upstream **MIT**; the unmodified copyright notice is preserved as `addons/dialogue_manager/LICENSE`. The released addon is installed in standard Godot `addons/dialogue_manager/`; its upstream `*.import` settings are retained because cold editor loading consumes them.
- `gate.dialogue` is ordinary upstream syntax, not an Ordivon parser.
- `story_root.gd` is a native Godot Control/button/view adapter. `gate_state.gd` owns the authoritative tokens/unlocked state and emits `state_changed`. The addon receives only an injected game state reference and evaluates the dialogue/choice conditions.

Run from `domains/game`:

    mise run test:dialogue-native

The existing Game Owner command imports the actual dialogue resource under the pinned Godot editor, then runs the native branch/state consumer and launches the normal main scene. The acceptance instantiates independent scenes; unlock spends exactly one token and changes the UI, leaving preserves state, and zero tokens disable the unlock response. Scenes are freed before quitting.

**Limits:** No save/resume, translation, audio, product quest integration, human playtest, physical keyboard/accessibility qualification or five-minute indie game has been established by this fixture. The provider is upstream code, not an Ordivon-wide engine or compiler.
