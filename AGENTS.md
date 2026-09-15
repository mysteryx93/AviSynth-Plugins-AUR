# Agent instructions — adding a package

This file is the procedure. Do not redesign the pipeline to add one plugin. Do not edit `.github/workflows/` unless the pipeline itself is broken.

Repo: `mysteryx93/AviSynth-Plugins-AUR`
Catalog: `catalog.yaml` (source of truth for ids, kinds, matrix)
PKGBUILDs: `packages/<aur>/PKGBUILD` (hand-written recipe)
Templates: `templates/{bin,source,script}.PKGBUILD`
Build helper: `scripts/build-package.sh <id> <distro> <version>`
Matrix helper: `scripts/catalog.py`

## Install paths

- AviSynth+ plugins and AVSI: `/usr/lib/avisynth/`
- VapourSynth plugins: `/usr/lib/vapoursynth/`
- VapourSynth Python modules: `site-packages`
- RIFE models (later): `/usr/lib/avisynth/models/` (same directory as the `.so`)

## Kinds

| `kind` | AUR | GitHub Release | When |
|---|---|---|---|
| `source` | User compiles — **required** for every compiled plugin | Arch + Ubuntu tarballs | Default. This is what Debian/Fedora would port. |
| `bin` | `-bin` fetches the **Arch** tarball from the source sibling’s Release | not compiled again | Optional extra for heavy builds (`binary_of: <source id>`) |
| `script` | Copy files | One `any` tarball | AVSI / Python only |

Never add `kind: bin` without a `kind: source` sibling. CI compiles the source id only.

## Naming

`aur` is **always** an explicit catalog field.

```
{avisynth|vapoursynth}-plugin-{name}[-{author}][-bin]
```

Include `{author}` when more than one implementation exists (pinterf vs classic mvtools, Asd-g RIFE vs other RIFE ports).

Never invent `conflicts`/`provides` against an existing AUR package unless the human explicitly wants to replace it. pinterf MVTools must **not** provide `avisynth-plugin-mvtools2` or `avisynth-plugin-mvtools2-git`.

## Add a package (checklist)

1. Read `catalog.yaml` and an existing package of the same `kind`.
2. Choose:
   - `id` — stable catalog key (`mvtools2-pinterf`, not the AUR name)
   - `aur` — apply the naming rule
   - `kind`, `host` (`avisynth` or `vapoursynth`), `author`, `repo`, `license`
   - `version_from`: `release` (GitHub latest release), `tag` (latest tag), or `manual` + `version`
3. Copy `templates/<kind>.PKGBUILD` → `packages/<aur>/PKGBUILD`. Fill `pkgname`, `pkgdesc`, `url`, `license`, `depends`, `source`, `package()`.
4. Append the catalog entry. Include `build` + `collect` (compiled) or `files` (script). The matrix picks it up; **do not** add a new workflow.
5. Dual-host plugins (AviSynth + VapourSynth, e.g. FrameRateConverter later) = **two** catalog ids and **two** PKGBUILDs, same `repo`.
5b. Heavy plugins (RIFE): source package **and** `-bin` with `binary_of: <source id>`. Two PKGBUILDs, one compile.
6. Test:
   - `python3 scripts/catalog.py --packages <id> matrix-build --from-pkgbuild`
   - `scripts/build-package.sh <id> ubuntu22.04 <version>` locally if you can
   - GitHub **Build** workflow, `packages` input = that `id`
7. Only after the build is green: maintainer runs **Publish** for that id (`AUR_SSH_PRIVATE_KEY` required).

Do **not** put third-party sources into this git tree. CI clones upstream at a tag.

## Catalog fields that matter to CI

- `submodules: true` — `git clone --recurse-submodules`
- `needs_avisynth_headers: true` — Arch `avisynthplus` or Ubuntu `HEADERS_ONLY` AviSynth+ install
- `cmake_min` — pip-install a newer CMake on Ubuntu 22.04 (RIFE needs 3.28)
- `collect[].glob` — paths relative to the clone; copied into the tarball under `dest_dir`
- `files[]` — script kind; `src` in the clone, `dest` in the tarball

## Release tarball names

```
{aur without -bin}-{version}-linux-x86_64-{arch|ubuntu22.04|any}.tar.zst
```

GitHub Release tag: `{source id}-v{version}` (example `rife-asdg-v1.4.1`). `-bin` uses the same tag via `binary_of`.

AUR `-bin` `source=` must point at the **Arch** tarball of that tag.

## What not to do

- Do not build `-bin` only on Ubuntu and ship that to the AUR. AUR `-bin` is Arch-built.
- Do not auto-publish on git push. Publish is `workflow_dispatch` or the weekly cron.
- Do not bundle the full RIFE model pack in the plugin package.
- Do not rename `id` after Publish; add a new package instead.
- Do not generate PKGBUILDs from YAML. Templates + a hand-written PKGBUILD.

## First packages (already in tree)

- `rife-asdg` → `avisynth-plugin-rife-asdg` (source) + `rife-asdg-bin` → `avisynth-plugin-rife-asdg-bin`
- `mvtools2-pinterf` → `avisynth-plugin-mvtools2-pinterf`
- `xclean-avs` → `avisynth-plugin-xclean` (AviSynth only; VS is already on the AUR as `vapoursynth-plugin-xclean-git`)
