#!/usr/bin/env bash
# Used on a disposable Publish checkout. Does not update this git repository.
set -euo pipefail
[[ $# -ge 2 && $# -le 4 ]] || { echo "Usage: $0 <PKGBUILD> <version> [pkgrel] [git_ref]" >&2; exit 2; }
pkgbuild=$1
version=$2
pkgrel=${3:-1}
git_ref=${4:-}
[[ "$version" =~ ^[a-zA-Z0-9][a-zA-Z0-9._+]*$ ]] || { echo "Invalid pkgver" >&2; exit 2; }
[[ "$pkgrel" =~ ^[1-9][0-9]*(\.[0-9]+)?$ ]] || { echo "Invalid pkgrel" >&2; exit 2; }
[[ -f "$pkgbuild" ]] || { echo "Missing $pkgbuild" >&2; exit 1; }
sed -i "s/^pkgver=.*/pkgver=${version}/" "$pkgbuild"
sed -i "s/^pkgrel=.*/pkgrel=${pkgrel}/" "$pkgbuild"
if [[ "$git_ref" =~ ^[a-f0-9]{40}$ ]] && grep -q "^_commit=" "$pkgbuild"; then
  sed -i "s/^_commit=.*/_commit='${git_ref}'/" "$pkgbuild"
fi
grep -E '^(pkgver|pkgrel|_commit)=' "$pkgbuild"
