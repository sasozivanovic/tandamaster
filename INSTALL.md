# Requirements

* [Python](https://www.python.org) (works with 3.13, and probably with some previous versions as well)

* [Qt5](https://www.qt.io/product/framework) (should be installed when installing Python module PyQt5)

* [GStreamer](https://gstreamer.freedesktop.org)

* Required Python modules (install via `pip`):

	* [PyQt5](https://pypi.org/project/PyQt5/)
	
	* [PyGObject](https://pypi.org/project/PyGObject/)
	
	* [mutagen](https://pypi.org/project/mutagen/)

	* [Unidecode](https://pypi.org/project/Unidecode/)
	
	* [bidict](https://pypi.org/project/bidict/)
	
	* [systemd-python](https://pypi.org/project/systemd-python/)
	
	* [pydantic](https://pypi.org/project/pydantic/)

* Optionally:

	* [libmp3splt](https://github.com/mp3splt/mp3splt/tree/master) (for automatic detection of silence at the beginning and the end of a song)
	
	* a TeX distribution, [TeX Live](https://tug.org/texlive/) or [MikTeX](https://miktex.org) (for printing out song info sheets)

# Installation

Arch Linux: TandaMaster is available via AUR: `yay -S tandamaster`

Other: `pipx install tandamaster`
	
# Configuration

The program can only be configured by manually editing a [TOML](https://toml.io) file.

After the program is run for the first time, it will copy the initial
configuration file to the standard location.  On Linux:
`~/.config/MilongueroSi/TandaMaster/config.toml`. See the comments in the file
itself for more information.  Note that this is where you set up library
folders.

The library database (`tandamaster.db`, in sqlite3 format), the global playtree
containing all the playtrees (`playtree.xml`) and the UI configuration
(`ui.xml`) reside in `~/.local/share/MilongueroSi/TandaMaster/config.toml`.

MilongueroSi? Visit the [site](https://milonguero.si)!
