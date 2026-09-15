# Porting (Debian, Fedora, …)

This repo does not ship those packages. Port `kind: source` and `kind: script` only — not `-bin`.

| Here | There |
|---|---|
| `packages/<aur>/PKGBUILD` | `debian/rules` / `.spec` |
| catalog `depends` / `makedepends` | mapped package names |
| catalog `build` | compile commands |
| catalog `submodules` | extra orig sources |
| `/usr/lib/avisynth/` | same if AviSynth+ autoloads it |

Release tarballs are not distro orig. Compile from upstream tags.

| Arch | Debian/Ubuntu | Fedora |
|---|---|---|
| `avisynthplus` | AviSynth+ headers (`-DHEADERS_ONLY=ON` if needed) | same |
| `vulkan-icd-loader` + `vulkan-headers` | `libvulkan-dev` | `vulkan-loader-devel` |
| `glslang` | `glslang-dev` | `glslang-devel` |
| `fftw` | `libfftw3-dev` | `fftw-devel` |
| `cmake` / `ninja` | `cmake` `ninja-build` | `cmake` `ninja-build` |

RIFE: CMake ≥ 3.28, `ncnn` + `avs_c_api_loader` submodules. The GitHub tag tarball omits them.
