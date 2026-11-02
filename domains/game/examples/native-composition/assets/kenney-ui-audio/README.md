# Native audio substitution consumer — Kenney CC0

The two WAV clips here are the complete set imported for this concrete consumer;
we do not vendor an unused pack or an Ordivon audio service.

- Original source and license: https://kenney.nl/assets/ui-audio — Kenney UI Audio, Creative Commons CC0 1.0.
- Godot-ready WAV distribution: https://github.com/Calinou/kenney-ui-audio at immutable commit `8c3d81b9159d058c444f89d12d518276b0b09345`, with the original `LICENSE.txt` copied here. The distributor documents its Ogg-to-WAV conversion.
- `click1.wav`: SHA256 `dd90b97f38b0ec7d52161d7c3bf8d61a66655766fd0af06439963351b4853a83`.
- `click2.wav`: SHA256 `a8b35cb35ff45738a9d7fe008490ad21a3ad30417dadd544a435d8b0ea84d841`.
- Real source consumers: `res://assert_audio.gd` and `res://movement_audio_feedback.gd`, which loads WAV resources and connects Godot native `AudioStreamPlayer` to actual `GridRules.state_changed` events.
- Contract: accepted turn advances trigger playback; rejected actions and resets do not. Swapping AudioStream resources does not change rules. Headless execution proves routing/native playback state, not physical speaker output or player enjoyment.
