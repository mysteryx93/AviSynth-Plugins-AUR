#!/usr/bin/env bash
# Used on a disposable Publish checkout. Does not update this git repository.
set -euo pipefail
[[ $# -ge 2 && $# -le 3 ]] || { echo "Usage: $0 <PKGBUILD> <version> [pkgrel]" >&2; exit 2; }
pkgbuild=$1
version=$2
pkgrel=${3:-1}
[[ "$version" =~ ^[a-zA-Z0-9][a-zA-Z0-9._+]*$ ]] || { echo "Invalid pkgver" >&2; exit 2; }
[[ "$pkgrel" =~ ^[1-9][0-9]*(\.[0-9]+)?$ ]] || { echo "Invalid pkgrel" >&2; exit 2; }
[[ -f "$pkgbuild" ]] || { echo "Missing $pkgbuild" >&2; exit 1; }
sed -i "s/^pkgver=.*/pkgver=${version}/" "$pkgbuild"
sed -i "s/^pkgrel=.*/pkgrel=${pkgrel}/" "$pkgbuild"
grep -E '^(pkgver|pkgrel)=' "$pkgbuild"
