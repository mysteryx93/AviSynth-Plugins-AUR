# Adding a package

Do not redesign the pipeline to add a plugin. Do not edit `.github/workflows/` unless it is broken.

`catalog.yaml` is the index. `packages/<aur>/PKGBUILD` is the recipe. Templates: `templates/{bin,source,script}.PKGBUILD`. Helpers: `scripts/build-package.sh`, `scripts/catalog.py`.

## Paths

- AviSynth: `/usr/lib/avisynth/`
- VapourSynth: `/usr/lib/vapoursynth/`, Python `site-packages`
- RIFE models (later): `/usr/lib/avisynth/models/`

## Kinds

| `kind` | AUR | Release | Notes |
|---|---|---|---|
| `source` | compiles | Arch + Ubuntu | Required for every compiled plugin |
| `bin` | Arch tarball from the source sibling’s Release | not compiled | Optional; `binary_of: <source id>` |
| `script` | copy files | `any` | AVSI / Python |

Never `bin` without `source`. CI compiles the source id only.

## Naming

`aur` is always explicit: `{avisynth|vapoursynth}-plugin-{name}[-{author}][-bin]`.

Author slug when implementations differ. No `conflicts`/`provides` against an existing AUR package unless the human wants a replacement. pinterf MVTools must not provide `avisynth-plugin-mvtools2` or `avisynth-plugin-mvtools2-git`.

## Checklist

1. Copy `templates/<kind>.PKGBUILD` → `packages/<aur>/PKGBUILD`.
2. Catalog row: `id`, `aur`, `kind`, `host`, `author`, `repo`, `license`, `version_from` (`release` / `tag` / `manual` + `version`), plus `build`+`collect` and/or `files`.
3. Dual-host (AviSynth + VapourSynth) = two ids, two PKGBUILDs. Heavy (RIFE) = source + `-bin`.
4. `files[]` — `src` in the clone, optional `dest`. `.so` / `.avsi` / `.py` go in `bin/` (the install payload; mixed is fine). `LICENSE` stays at the root. `install.txt` is the readme.
5. `python3 scripts/catalog.py --packages <id> matrix-build --from-pkgbuild`, then GitHub **Build**. Maintainer **Publish**.

Do not vendor upstream. Keep `_commit`, catalog `version`, and `pkgver` in sync for `version_from: manual`.

## CI fields

- `submodules: true`
- `needs_avisynth_headers: true`
- `cmake_min` (Ubuntu 22.04; RIFE needs 3.28)
- `defaults.gcc` (CI compiler on Arch and Ubuntu; 15 = extra/gcc15 + jammy toolchain PPA)
- `collect[].glob` (into `bin/` unless `dest_dir` is set)
- `files[]` — `src` in the clone, optional `dest` (default: archive root)

Tarball: `bin/` (whatever AviSynth loads: `.so`, `.avsi`, or both), `LICENSE` if present, `install.txt`. Name: `{source aur}-{version}-linux-x86_64-{arch|ubuntu22.04|any}.tar.zst`. Tag: `{source id}-v{version}`. `-bin` copies `bin/` from the **Arch** tarball of that tag.

Do not: ship Ubuntu-built AUR `-bin`; publish on push; bundle RIFE models; rename `id` after Publish; generate PKGBUILDs from YAML.

**Build** is the compile-and-test gate (PR/dispatch, artifacts only — never a Release). **Publish** is optional Release then AUR. Dispatch does **not** compile unless you tick `compile`; it takes tarballs from the latest successful Build on the branch, or `build_run_id`. Dispatch defaults to a **draft** Release and skips AUR (`-bin` cannot fetch draft assets). Uncheck `draft` to publish the Release and push AUR. Uncheck `create_release` for AUR-only (source/script). Monday cron always compiles, publishes the Release, and pushes AUR. AUR `makepkg --test` is skipped for `kind: source` (that would compile a third time). Cron compares AUR `pkgver`; this repo’s PKGBUILDs are not updated by Publish — bump `pkgrel` for same-version recipe changes.

Secrets: `AUR_SSH_PRIVATE_KEY`, optional `AUR_USERNAME` / `AUR_EMAIL` (default `Hanuman` / `mysteryx93@protonmail.com`).

