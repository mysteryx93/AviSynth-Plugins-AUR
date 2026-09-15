# AviSynth-Plugins-AUR

Packaging repo for **AviSynth+** (and later VapourSynth) plugins on Arch Linux.

It does three things:

1. **AUR packages** — `PKGBUILD`s pushed with GitHub Actions
2. **GitHub Releases** — Arch **and** Ubuntu 22.04 tarballs of the built plugins, so non-Arch users can drop a `.so` / `.avsi` in place
3. **A catalog** — add a plugin by editing `catalog.yaml` and dropping a `PKGBUILD`, not by inventing a new workflow

Maintainer AUR account: **Hanuman**.

## Packages

| Catalog id | AUR name | Kind | Upstream |
|---|---|---|---|
| `rife-asdg` | `avisynth-plugin-rife-asdg` | source (the recipe) | [Asd-g/AviSynthPlus-RIFE](https://github.com/Asd-g/AviSynthPlus-RIFE) |
| `rife-asdg-bin` | `avisynth-plugin-rife-asdg-bin` | prebuilt Arch binary | same |
| `mvtools2-pinterf` | `avisynth-plugin-mvtools2-pinterf` | source | [pinterf/mvtools](https://github.com/pinterf/mvtools) |
| `xclean-avs` | `avisynth-plugin-xclean` | AVSI script | [mysteryx93/xClean](https://github.com/mysteryx93/xClean) |

Every compiled plugin has a **source** package. `-bin` is optional Arch convenience (RIFE’s ncnn/Vulkan build is slow). Debian/Fedora porters should use the source `PKGBUILD` + catalog entry — see [docs/PORTING.md](docs/PORTING.md).

Names include the **author/fork** when more than one implementation exists. pinterf’s MVTools2 is not classic Fizick MVTools and is not `vapoursynth-plugin-mvtools`. This repo does **not** `provides`/`conflicts` those other packages.

## Install

Arch (AUR):

```bash
yay -S avisynth-plugin-mvtools2-pinterf
yay -S avisynth-plugin-rife-asdg-bin   # or avisynth-plugin-rife-asdg to compile locally
yay -S avisynth-plugin-xclean
```

Ubuntu / anyone else: download the `*-linux-x86_64-ubuntu22.04.tar.zst` (or `*-any.tar.zst` for scripts) from [Releases](https://github.com/mysteryx93/AviSynth-Plugins-AUR/releases) and copy files into `/usr/lib/avisynth/` (see `install.txt` inside the archive). Ubuntu tarballs target **22.04**; compatible host libraries and plugin runtime dependencies are still required on each system.

AviSynth+ autoloads `.so` and `.avsi` from `/usr/lib/avisynth/`.

RIFE models are **not** in the plugin package. Pass `model_path` or wait for `avisynth-plugin-rife-asdg-models`.

## Naming

```
{avisynth|vapoursynth}-plugin-{name}[-{author}][-bin]
```

- Put the author/fork slug in the name when implementations differ.
- `aur` in `catalog.yaml` is explicit. It is never generated from `author`.
- `-bin` is additive. The source package always exists so the recipe can be rebuilt (AUR, or a future Debian/Fedora repo).

## Propose a new package

1. Fork this repo.
2. Read `AGENTS.md` if you are an agent; otherwise copy `templates/{bin,source,script}.PKGBUILD` to `packages/<aur>/PKGBUILD`.
3. Add a row to `catalog.yaml` (`id`, `aur`, `kind`, `host`, `author`, `repo`, build/collect or files).
4. Open a pull request. `build.yml` compiles Arch + Ubuntu (or packs the script) and uploads artifacts.
5. Only the maintainer runs **Publish** (AUR SSH key). Contributors do not need secrets.

Do not vendor upstream sources in this git tree. The `PKGBUILD` and CI clone the upstream tag.

## Workflows

| Workflow | When | What |
|---|---|---|
| **Build** | PR, `workflow_dispatch` | Artifacts only |
| **Publish** | `workflow_dispatch`, Monday cron | Tarballs → GitHub Release → AUR |

Pushing to `main` does not publish.

The weekly check compares upstream versions with the AUR's published `pkgver`.
Manual Publish rebuilds the selected packages; publishing does not update this
repository's PKGBUILDs. Keep their versions current separately so PR builds test
the intended versions. Increment `pkgrel` when republishing a changed recipe at
the same upstream version.

## Local validation

```bash
python3 -m unittest discover -s tests
python3 scripts/catalog.py matrix-build --from-pkgbuild
```

Python requires PyYAML. Full builds install system dependencies; run the build
helper in a disposable Arch container or Ubuntu 22.04 environment. Work directories
and tarballs remain under `out/` for inspection. Manual script packages use the
PKGBUILD's pinned `_commit`; update it alongside the catalog version and `pkgver`.

Maintainer secrets: `AUR_SSH_PRIVATE_KEY`, optional `AUR_USERNAME` / `AUR_EMAIL` (default `Hanuman` / `mysteryx93@protonmail.com`). Same names as SynthMultiViewer.

## License

This packaging repo is MIT. Each plugin keeps its upstream license in its `PKGBUILD`.
