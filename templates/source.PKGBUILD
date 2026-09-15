# Maintainer: Etienne Charland <mysteryx93 at protonmail dot com>
# Copy to packages/<aur>/PKGBUILD and fill the fields.
# Every compiled plugin needs this source package, even if a -bin also exists.

pkgname=avisynth-plugin-NAME-AUTHOR
pkgver=0.0.0
pkgrel=1
pkgdesc="AviSynth+ plugin"
arch=('x86_64')
url='https://github.com/UPSTREAM/REPO'
license=('GPL-2.0-only')
depends=('avisynthplus')
makedepends=('cmake')
source=("${pkgname}-${pkgver}.tar.gz::https://github.com/UPSTREAM/REPO/archive/refs/tags/${pkgver}.tar.gz")
sha256sums=('SKIP')

build() {
    cmake -S "REPO-${pkgver}" -B build \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX=/usr
    cmake --build build
}

package() {
    DESTDIR="${pkgdir}" cmake --install build
}
