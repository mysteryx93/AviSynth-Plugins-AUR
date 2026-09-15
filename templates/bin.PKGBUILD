# Maintainer: Etienne Charland <mysteryx93 at protonmail dot com>
# Requires a kind: source sibling and catalog binary_of.

pkgname=avisynth-plugin-NAME-AUTHOR-bin
pkgver=0.0.0
pkgrel=1
pkgdesc="AviSynth+ plugin (prebuilt)"
arch=('x86_64')
url='https://github.com/UPSTREAM/REPO'
license=('MIT')
depends=('avisynthplus')
provides=("avisynth-plugin-NAME-AUTHOR=${pkgver}")
conflicts=('avisynth-plugin-NAME-AUTHOR')
options=('!strip')
_tarball="avisynth-plugin-NAME-AUTHOR-${pkgver}-linux-x86_64-arch.tar.zst"
source=("${_tarball}::https://github.com/mysteryx93/AviSynth-Plugins-AUR/releases/download/ID-v${pkgver}/${_tarball}")
sha256sums=('SKIP')

package() {
    install -dm755 "${pkgdir}/usr/lib/avisynth"
    cp -a "${srcdir}/bin/." "${pkgdir}/usr/lib/avisynth/"
}
