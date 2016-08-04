exe:
	python -m PyInstaller -y tandamaster.spec

mp3splt_h.py: libmp3splt-0.9.2/src/splt.h libmp3splt-0.9.2/include/libmp3splt/mp3splt.h
	ctypesgen.py -lmp3splt -Ilibmp3splt-0.9.2/include/libmp3splt libmp3splt-0.9.2/src/splt.h > mp3splt_h.py
	2to3 -w mp3splt_h.py
	sed -if patch.mp3splt_h.py.sed mp3splt_h.py
