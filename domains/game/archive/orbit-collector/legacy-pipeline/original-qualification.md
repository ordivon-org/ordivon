## Orbit Collector Linux qualification — current G07 consumer contract

**Current owner:** Game. **Natural providers:** Rust/Cargo and Bevy for build and native graphics, Xvfb/Mesa/Vulkan for the CI graphical environment, GitHub Actions for published preview Artifacts. The existing G07 R2.1 contract lives in [the Game LEGO plan](../planning/lego-plan-r1.json); this section is a *consumer requirement*, not another LEGO or a workflow service.

Two outcomes must not be confused:

- **Build only:** `mise run factory:build:bevy` validates the locked Rust/Bevy source, tests the native ECS consumer, and builds `ordivon-orbit-collector`. It does not require a running display and must not assert graphics, player input, or distributable-preview qualification.
- **Verified Linux preview:** `mise run factory:package:orbit-linux` calls the *same* `scripts/package_orbit_linux.sh` used by `.github/workflows/game-orbit-factory.yml`. It requires a nonempty binary, `xvfb-run` and GNU `timeout`, a real native window and `AdapterInfo` witness, and a 14-second timeout-expiry diagnostic. Only then may it publish an archive containing source and binary digests, launch log, smoke receipt, instructions, and license. A child exiting 124 early is **not** a valid timeout witness.

**Failure and evidence boundary:** missing prerequisites => `ENV_BLOCKED`/nonzero; absent or failed native window/adapter smoke => failure/nonzero; both must suppress `ORBIT_FACTORY_LINUX_PREVIEW_READY` and a current candidate archive. The native negative tests in `scripts/test_orbit_package_contract.py` check missing tools and premature 124; they do **not** simulate a GPU. A successful CI Xvfb smoke does not establish actual player-visible frames, Windows operation, physical GPU performance, or Human enjoyment. Preserve `UNKNOWN` for those claims.

**Recheck the actual consumer:**

```sh
cd domains/game
mise run test:orbit-package-contract
mise run factory:build:bevy
mise run factory:package:orbit-linux  # only on a host with qualified graphics
```

The separate native GitHub workflow is the remote graphical-acceptance and Artifact producer. Inspect its exact run SHA/status before reporting a new release or real player acceptance. Generic `mise run verify` does not imply Linux graphical packaging passed.

**Historical incident (closed code change, not an instruction to re-execute the old plan):** at SourceCut `8346863be965da34371944679d063fd9fd0358ac`, the old packaging task could print `NOT_RUN` and `READY` together when Xvfb or timeout was missing. PR [#2002](https://github.com/ordivon-org/ordivon/pull/2002) replaced that path with the existing fail-closed script and shared CI invocation. The original proof discussion and completed step-by-step execution ledger remain available in Git history. Do not re-create a second package service, test farm, scheduler, or duplicate execution checklist.
