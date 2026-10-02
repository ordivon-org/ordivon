# Real Chrome user-session provider

This provider binds a persistent Windows Google Chrome carrier to the logged-in interactive
user through Windows Task Scheduler. Windows Runtime may invoke the provider, but the scheduled
task owns the browser process lifetime after the finite Runtime Job ends.

The provider does not grant BrowserControlAuthority or ProviderEffectAuthority. Chrome remote
debugging consent remains an explicit human gate. The default browser network binding is the
dedicated Network v2 Windows Real Chrome proxy at http://127.0.0.1:19781.

The materializer only copies exact source bytes to a content-addressed ProgramData path. It does
not register, start, stop, or remove a scheduled task.
