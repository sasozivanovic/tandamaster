# Maintainer: Sašo Živanović <saso.zivanovic@guest.arnes.si>
pkgname=tandamaster-git
_pkgname=${pkgname%-git}
pkgrel=1
epoch=
pkgdesc="A music player specialized for playing music at milongas"
arch=('any')
url="https://github.com/sasozivanovic/tandamaster"
license=('GPL')
groups=()
depends=(
  'qt5-base'
  'python-pyqt5'
  'gstreamer'
  # 'ipython' # temporary, for debugging purposes
  'python-mutagen'
  'python-unidecode'
  'python-bidict'
  'python-systemd'
  'python-pydantic'
)
makedepends=('python-ctypesgen')
checkdepends=()
optdepends=('libmp3splt: silence detection support')
provides=()
conflicts=()
replaces=()
backup=()
options=()
install=
changelog=
source=("git+https://github.com/sasozivanovic/tandamaster.git")
#noextract=()
md5sums=('SKIP')
validpgpkeys=()

pkgver() {
    cd "$srcdir/$_pkgname"
    printf "r%s.%s" "$(git rev-list --count HEAD)" "$(git rev-parse --short HEAD)"
}

prepare() {
    cd "$_pkgname"
    ctypesgen -lmp3splt /usr/include/libmp3splt/mp3splt.h -o src/tandamaster/mp3splt_h.py
}

#build() {
#	cd "$pkgname-$pkgver"
#	./configure --prefix=/usr
#	make
#}

#check() {
#	cd "$pkgname-$pkgver"
#	make -k check
#}

package() {
    cd "$_pkgname"
    install -D -m644 "$_pkgname/LICENSE" "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
    #install -D -m755 "$_pkgname/${_pkgname}" "$pkgdir/usr/bin/${_pkgname}"
    
}
