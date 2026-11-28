# Native audio substitution consumer — Kenney CC0

The two WAV clips here are the complete set imported for this concrete consumer;
we do not vendor an unused pack or an Ordivon audio service.

- Original source and license: https://kenney.nl/assets/ui-audio — Kenney UI Audio, Creative Commons CC0 1.0.
- Godot-ready WAV distribution: https://github.com/Calinou/kenney-ui-audio at immutable commit `8c3d81b9159d058c444f89d12d518276b0b09345`, with the original `LICENSE.txt` copied here. The distributor documents its Ogg-to-WAV conversion.
- `click1.wav`: SHA256 `dd90b97f38b0ec7d52161d7c3bf8d61a66655766fd0af06439963351b4853a83`.
- `click2.wav`: SHA256 `a8b35cb35ff45738a9d7fe008490ad21a3ad30417dadd544a435d8b0ea84d841`.
- Real native consumer: `main.tscn` creates `MovementAudio`; `composition_root.gd` loads the initial WAV and binds `movement_audio_feedback.gd` to actual `GridRules.state_changed`. `assert_audio.gd` validates the installed scene and replacement clip.
- Contract: accepted turn advances trigger playback; rejected actions and resets do not. Swapping AudioStream resources does not change rules. Headless execution proves routing/native playback state, not physical speaker output or player enjoyment.

**Recursive LEGO R2.1 (this concrete native audio carrier):**
`I` = bounded state_changed snapshot + selected AudioStream; `O` = native playback request; `S` = last observed turn; `pre` = a ready AudioStreamPlayer and bound real rules; `post` = each observed positive turn advance initiates playback, while no advance initiates none; `inv` = no Game rule-state ownership in sound; `eff` = AudioStreamPlayer.play(); `c` = constant event work; `epsilon` = physical speaker delivery and player experience unmeasured; `prov` = immutable upstream commit plus WAV SHA-256 and copied CC0 license; `unfold` = Godot signal+audio resource+player and the actual scene consumer. This is not a universal audio or game theorem.
