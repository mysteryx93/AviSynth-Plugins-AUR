#!/usr/bin/env bash
# Build one catalog package for one distro and write a .tar.zst into out/.
set -euo pipefail

usage() {
  echo "Usage: $0 <package-id> <distro> <version>" >&2
  echo "  distro: arch | ubuntu22.04 | any" >&2
  exit 2
}

[[ $# -eq 3 ]] || usage

ID=$1
DISTRO=$2
VERSION=$3
[[ "$ID" =~ ^[a-z0-9][a-z0-9-]*$ ]] || usage
[[ "$DISTRO" =~ ^(arch|ubuntu22\.04|any)$ ]] || usage
[[ "$VERSION" =~ ^[a-zA-Z0-9][a-zA-Z0-9._+]*$ ]] || usage

ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
OUT="$ROOT/out"
# Fresh images have no PyYAML; catalog.py needs it before the rest of the deps.
if [[ "$DISTRO" == arch ]]; then
  pacman -Syu --noconfirm --needed python python-yaml
else
  sudo apt-get update
  sudo apt-get install -y --no-install-recommends python3 python3-yaml
fi

META=$(python3 "$ROOT/scripts/catalog.py" get "$ID")
json_get() {
  python3 -c 'import json,sys; d=json.load(sys.stdin); p=sys.argv[1].split(".");
v=d
for k in p:
    if isinstance(v, dict):
        v=v.get(k)
    else:
        v=None
print("" if v is None else v if not isinstance(v, (dict, list)) else json.dumps(v))' "$1" <<<"$META"
}

KIND=$(json_get kind)
# -bin is packed from the source sibling's Arch tarball, not compiled here.
[[ "$KIND" != bin ]] || { echo "Build the binary_of source package instead" >&2; exit 1; }
if [[ "$KIND" == script ]]; then
  [[ "$DISTRO" == any ]] || usage
else
  [[ "$DISTRO" != any ]] || usage
fi
mkdir -p "$OUT"
WORK=$(mktemp -d "$OUT/work-$ID-$DISTRO.XXXXXXXX")
STAGE="$WORK/stage"
mkdir -p "$STAGE" "$WORK/src"
REPO=$(json_get repo)
HOST=$(json_get host)
AUR=$(json_get aur)
SUBMODULES=$(json_get submodules)
NEEDS_AVS=$(json_get needs_avisynth_headers)
CMAKE_MIN=$(json_get cmake_min)
GCC_VER=$(json_get gcc)
INSTALL_HINT=$(json_get install_hint)
BUILD=$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("build") or "")' <<<"$META")
# ubuntu22.04 → catalog key ubuntu
mapfile -t BUILD_DEPS < <(python3 -c 'import json,sys; [print(dep) for dep in json.load(sys.stdin).get("makedepends", {}).get(sys.argv[1], [])]' "${DISTRO%%22.04}" <<<"$META")
# Arch names. CMake often needs the runtime .so (e.g. libvulkan) at configure time.
mapfile -t RUN_DEPS < <(python3 -c 'import json,sys; [print(dep) for dep in json.load(sys.stdin).get("depends") or []]' <<<"$META")
COLLECT=$(python3 -c 'import json,sys; print(json.dumps(json.load(sys.stdin).get("collect") or []))' <<<"$META")
FILES=$(python3 -c 'import json,sys; print(json.dumps(json.load(sys.stdin).get("files") or []))' <<<"$META")

install_avisynth_headers() {
  if [[ "$NEEDS_AVS" != "True" && "$NEEDS_AVS" != "true" ]]; then
    return 0
  fi
  if pkg-config --exists avisynth 2>/dev/null; then
    echo "avisynth headers already present"
    return 0
  fi
  if [[ -f /usr/include/avisynth/avisynth.h || -f /usr/local/include/avisynth/avisynth.h ]]; then
    echo "avisynth.h already installed"
    return 0
  fi
  echo "Installing AviSynth+ headers (HEADERS_ONLY)"
  local avs="$WORK/AviSynthPlus"
  local avs_url="https://github.com/AviSynth/AviSynthPlus.git"
  # Latest release tag (not master): Version.cmake needs git describe, and a
  # shallow master clone has no tags. ls-remote so this tracks new AviSynth+ releases.
  local tag
  tag=$(git ls-remote --tags --refs "$avs_url" \
    | awk -F/ '{print $NF}' \
    | grep -E '^v[0-9]' \
    | grep -viE 'pre|rc|alpha|beta' \
    | sort -V | tail -1)
  [[ -n "$tag" ]] || { echo "Could not resolve an AviSynth+ release tag" >&2; exit 1; }
  echo "AviSynth+ headers $tag"
  git clone --depth 1 --branch "$tag" "$avs_url" "$avs"
  # Ubuntu has no avisynthplus package; headers-only is enough to compile plugins.
  cmake -S "$avs" -B "$avs/build" -DHEADERS_ONLY:BOOL=ON -DCMAKE_BUILD_TYPE=Release
  # cmake --install does not run VersionGen; without it version.h is missing.
  cmake --build "$avs/build" --target VersionGen
  if (( EUID == 0 )); then
    cmake --install "$avs/build"
  else
    sudo cmake --install "$avs/build"
  fi
}

install_gcc() {
  [[ "$KIND" != script ]] || return 0
  local ver=${GCC_VER:-}
  [[ -n "$ver" ]] || return 0
  if ! command -v "g++-$ver" >/dev/null; then
    case "$DISTRO" in
      arch)
        # extra/gcc15; gcc13/14 are AUR and would compile the compiler.
        pacman -S --noconfirm --needed "gcc${ver}"
        ;;
      ubuntu22.04)
        sudo apt-get install -y --no-install-recommends software-properties-common
        sudo add-apt-repository -y ppa:ubuntu-toolchain-r/test
        sudo apt-get update
        sudo apt-get install -y --no-install-recommends "gcc-$ver" "g++-$ver"
        ;;
      *) return 0 ;;
    esac
  fi
  command -v "g++-$ver" >/dev/null || {
    echo "g++-$ver not installed (catalog defaults.gcc=$ver)" >&2
    exit 1
  }
  export CC="gcc-$ver" CXX="g++-$ver"
  echo "Using $CXX"
}

install_cmake_min() {
  local need=${CMAKE_MIN:-}
  [[ -n "$need" ]] || return 0
  if command -v cmake >/dev/null; then
    python3 - "$need" <<'PY' && return 0
import sys, subprocess
need = tuple(int(x) for x in sys.argv[1].split("."))
out = subprocess.check_output(["cmake", "--version"], text=True).splitlines()[0]
ver = tuple(int(x) for x in out.split()[-1].split(".")[:3])
sys.exit(0 if ver >= need else 1)
PY
  fi
  echo "Installing CMake >= $need"
  pip3 install --user "cmake>=${need}"
  export PATH="$HOME/.local/bin:$PATH"
}

setup_arch() {
  pacman -S --noconfirm --needed \
    base-devel git python-pip cmake pkgconf zstd "${BUILD_DEPS[@]}" "${RUN_DEPS[@]}"
}

setup_ubuntu() {
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    ca-certificates git python3 python3-pip python3-yaml python3-venv \
    build-essential pkg-config zstd cmake "${BUILD_DEPS[@]}"
  export PATH="$HOME/.local/bin:$PATH"
}

case "$DISTRO" in
  arch) setup_arch ;;
  ubuntu22.04|any) setup_ubuntu ;;
  *) echo "Unknown distro: $DISTRO" >&2; exit 1 ;;
esac

install_cmake_min
install_gcc
install_avisynth_headers

SRC="$WORK/src/upstream"
GIT_BRANCH=$(json_get git_branch)
clone_upstream() {
  local extra=()
  if [[ "$SUBMODULES" == "True" || "$SUBMODULES" == "true" ]]; then
    extra+=(--recurse-submodules --shallow-submodules)
  fi
  if [[ "$KIND" == "script" ]] && [[ "$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("version_from"))' <<<"$META")" == "manual" ]]; then
    git clone "${extra[@]}" "$REPO" "$SRC"
    local commit
    # Same pin as the PKGBUILD; catalog version alone is not a git ref.
    commit=$(sed -n "s/^_commit='\([a-f0-9]*\)'$/\1/p" "$ROOT/packages/$AUR/PKGBUILD")
    [[ "$commit" =~ ^[a-f0-9]{40}$ ]] || { echo "Manual scripts require a pinned _commit in PKGBUILD" >&2; exit 1; }
    git -C "$SRC" checkout --detach "$commit"
    return
  fi
  # git_branch is the tree to clone when GitHub's default is not the Linux source.
  if [[ -n "$GIT_BRANCH" ]]; then
    git clone "${extra[@]}" --branch "$GIT_BRANCH" "$REPO" "$SRC"
  else
    git clone "${extra[@]}" "$REPO" "$SRC"
  fi
  git -C "$SRC" fetch --tags --force
  git -C "$SRC" fetch origin "refs/tags/${VERSION}:refs/tags/${VERSION}" 2>/dev/null || true
  git -C "$SRC" fetch origin "refs/tags/v${VERSION}:refs/tags/v${VERSION}" 2>/dev/null || true
  if git -C "$SRC" checkout --detach "$VERSION"; then
    return
  fi
  if git -C "$SRC" checkout --detach "v${VERSION}"; then
    return
  fi
  echo "No git ref $VERSION (or v$VERSION) in $REPO${GIT_BRANCH:+ (git_branch $GIT_BRANCH)}" >&2
  exit 1
}

clone_upstream

if [[ "$KIND" != "script" && -n "$BUILD" ]]; then
  (
    cd "$SRC"
    export DISTRO CC CXX
    # shellcheck disable=SC2086
    bash -euo pipefail -c "$BUILD"
  )
fi

python3 - "$SRC" "$STAGE" "$COLLECT" "$FILES" <<'PY'
import glob, json, os, shutil, sys
src, stage, collect_raw, files_raw = sys.argv[1:5]
collect = json.loads(collect_raw)
files = json.loads(files_raw)
copied = 0
for item in collect:
    pattern = os.path.join(src, item["glob"])
    matches = glob.glob(pattern, recursive=True)
    if not matches:
        raise SystemExit(f"collect glob matched nothing: {item['glob']}")
    # Payload lives in bin/; LICENSE and install.txt stay at the archive root.
    dest_dir = os.path.join(stage, item.get("dest_dir") or "bin")
    os.makedirs(dest_dir, exist_ok=True)
    for path in matches:
        shutil.copy2(path, os.path.join(dest_dir, os.path.basename(path)))
        copied += 1
PAYLOAD_EXT = {".so", ".avsi", ".py", ".dll"}
for item in files:
    src_path = os.path.join(src, item["src"])
    name = os.path.basename(item["src"])
    if item.get("dest"):
        rel = item["dest"]
    elif os.path.splitext(name)[1].lower() in PAYLOAD_EXT:
        rel = os.path.join("bin", name)
    else:
        rel = name
    dest_path = os.path.join(stage, rel)
    parent = os.path.dirname(dest_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    shutil.copy2(src_path, dest_path)
    copied += 1
if copied == 0:
    raise SystemExit("no files collected")
print(f"staged {copied} file(s)")
PY

HINT=${INSTALL_HINT:-"Install files under the matching AviSynth+ or VapourSynth plugin directory."}
if [[ "$HOST" == "avisynth" ]]; then
  DEFAULT_DIR="/usr/lib/avisynth"
else
  DEFAULT_DIR="/usr/lib/vapoursynth"
fi
cat > "$STAGE/install.txt" <<EOF
Package: $AUR
Version: $VERSION
Distro: $DISTRO
Host: $HOST

$HINT

Copy everything in bin/ into: $DEFAULT_DIR
EOF

TARBALL="${AUR}-${VERSION}-linux-x86_64-${DISTRO}.tar.zst"

(
  cd "$STAGE"
  tar --zstd -cf "$OUT/$TARBALL" .
)
echo "Wrote $OUT/$TARBALL"
ls -lh "$OUT/$TARBALL"
