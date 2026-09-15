#!/usr/bin/env bash
set -euo pipefail
pkgbuild=$1
version=$2
pkgrel=${3:-1}
[[ -f "$pkgbuild" ]] || { echo "Missing $pkgbuild" >&2; exit 1; }
sed -i "s/^pkgver=.*/pkgver=${version}/" "$pkgbuild"
sed -i "s/^pkgrel=.*/pkgrel=${pkgrel}/" "$pkgbuild"
grep -E '^(pkgver|pkgrel)=' "$pkgbuild"
