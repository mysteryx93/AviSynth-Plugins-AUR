# Porting these packages (Debian, Fedora, …)

This repo does **not** ship Debian or Fedora packages. The AUR **source** `PKGBUILD` plus the matching `catalog.yaml` entry is the recipe someone else can translate.

`-bin` packages are Arch-only convenience. Do not port them. Port `kind: source` and `kind: script`.

## What to copy

For each plugin:

| This repo | Becomes |
|---|---|
| `packages/<aur>/PKGBUILD` (`kind: source` or `script`) | `debian/rules` / `.spec` build + install |
| `catalog.yaml` `depends` / `makedepends` | package dependencies (map names) |
| `catalog.yaml` `build` | the actual compile commands |
| `catalog.yaml` `submodules` | extra orig tarballs / vendored sources |
| install path `/usr/lib/avisynth/` | same on Debian/Fedora if AviSynth+ autoloads that dir |

GitHub Release tarballs (`*-ubuntu22.04.tar.zst`) are a shortcut for users, not a distro source. Distro packages should compile from upstream tags.

## Dependency name hints

| Arch | Debian/Ubuntu | Fedora |
|---|---|---|
| `avisynthplus` | headers from AviSynth+ (`-DHEADERS_ONLY=ON` if no distro package) | same |
| `vulkan-icd-loader` + `vulkan-headers` | `libvulkan-dev` | `vulkan-loader-devel` |
| `glslang` | `glslang-dev` | `glslang-devel` |
| `fftw` | `libfftw3-dev` | `fftw-devel` |
| `cmake` / `ninja` | `cmake` `ninja-build` | `cmake` `ninja-build` |

RIFE needs CMake ≥ 3.28 and the `ncnn` + `avs_c_api_loader` git submodules (ncnn pulls glslang). The GitHub tag tarball does **not** include submodules; use `git submodule update --init --recursive` or extra orig sources.

## Policy we keep here

Every compiled plugin has a source AUR package even when a `-bin` also exists (RIFE). That source package is what a Debian/Fedora repo would rebuild.

If you start that repo, point it at this catalog rather than scraping `-bin` tarballs.
