mp3splt_h.py: PHONY
	ctypesgen.py -lmp3splt -Ilibmp3splt-0.9.2/include/libmp3splt libmp3splt-0.9.2/src/splt.h > mp3splt_h.py
	2to3 -w mp3splt_h.py

_trim.so: trim.i trim.c
	swig -python trim.i
	gcc -c -fPIC trim.c trim_wrap.c -I/usr/include/python3.5m -I/usr/include/libmp3splt
	gcc -shared trim.o trim_wrap.o  -lmp3splt -o _trim.so

trim.a: trim.c
	gcc -o trim.a trim.c -I/usr/include/libmp3splt -lmp3splt

PHONY:
