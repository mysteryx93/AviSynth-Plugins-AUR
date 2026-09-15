# AviSynth-Plugins-AUR

Linux packaging for AviSynth+ plugins.

1. **AUR** — `PKGBUILD`s, account **Hanuman**
2. **GitHub Releases** — Arch and Ubuntu 22.04 tarballs (`.so` / `.avsi`)
3. **`catalog.yaml`** — add a plugin with a `PKGBUILD`, not a new workflow

AviSynth+ autoloads from `/usr/lib/avisynth/`.

**Arch:** install from the AUR. Prefer `-bin` when it exists; otherwise the source package compiles locally.

**Anywhere else:** [Releases](https://github.com/mysteryx93/AviSynth-Plugins-AUR/releases) — `*-ubuntu22.04.tar.zst` or `*-any.tar.zst`, then follow `install.txt`. Tarballs are 22.04; you still need the plugin’s runtime libraries.

Every compiled plugin has a **source** recipe. `-bin` is optional. A Debian/Fedora repo would port source and script packages only — [docs/PORTING.md](docs/PORTING.md).

## Packages

| Package | Notes |
|---|---|
| `avisynth-plugin-rife-asdg` / `-bin` | [Asd-g RIFE](https://github.com/Asd-g/AviSynthPlus-RIFE). Models not included — unpack [the pack](https://github.com/Asd-g/AviSynthPlus-RIFE/releases/tag/models) into `/usr/lib/avisynth/models/` or pass `model_path`. `-bin` is the prebuilt. |
| `avisynth-plugin-mvtools2-pinterf` | [pinterf branch](https://github.com/pinterf/mvtools). |
| `avisynth-plugin-xclean` | [xClean](https://github.com/mysteryx93/xClean) AVSI. VapourSynth is already `vapoursynth-plugin-xclean-git`. |

## Add a plugin

`packages/<aur>/PKGBUILD` + a row in `catalog.yaml`. Procedure: `AGENTS.md`. Open a PR; **Build** produces artifacts. Only the maintainer runs **Publish** (Release, then AUR). Pushing to `main` does not publish.

## License

MIT packaging. Each plugin keeps its upstream license.
