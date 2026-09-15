# Maintainer: Etienne Charland <mysteryx93 at protonmail dot com>
# Copy to packages/<aur>/PKGBUILD and fill the fields.
# Optional. Requires a kind: source sibling and catalog binary_of: <source id>.

pkgname=avisynth-plugin-NAME-AUTHOR-bin
pkgver=0.0.0
pkgrel=1
pkgdesc="AviSynth+ plugin (prebuilt)"
arch=('x86_64')
url='https://github.com/UPSTREAM/REPO'
license=('MIT')
depends=('avisynthplus')
provides=('avisynth-plugin-NAME-AUTHOR')
conflicts=('avisynth-plugin-NAME-AUTHOR')
options=('!strip')
_tarball="avisynth-plugin-NAME-AUTHOR-${pkgver}-linux-x86_64-arch.tar.zst"
source=("${_tarball}::https://github.com/mysteryx93/AviSynth-Plugins-AUR/releases/download/ID-v${pkgver}/${_tarball}")
sha256sums=('SKIP')

package() {
    install -dm755 "${pkgdir}/usr/lib/avisynth"
    install -m755 "${srcdir}"/usr/lib/avisynth/*.so "${pkgdir}/usr/lib/avisynth/"
    # Include upstream license files in the release and install them here.
}
