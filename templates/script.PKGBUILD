# Maintainer: Etienne Charland <mysteryx93 at protonmail dot com>

pkgname=avisynth-plugin-NAME
pkgver=0.0.0
pkgrel=1
pkgdesc="AviSynth script plugin (AVSI)"
arch=('any')
url='https://github.com/UPSTREAM/REPO'
license=('GPL-3.0-only')
depends=('avisynthplus')
_commit='REPLACE_WITH_COMMIT'
source=("${pkgname}-${pkgver}.tar.gz::https://github.com/UPSTREAM/REPO/archive/${_commit}.tar.gz")
sha256sums=('SKIP')

package() {
    cd "REPO-${_commit}"
    install -Dm644 NAME.avsi "${pkgdir}/usr/lib/avisynth/NAME.avsi"
}
