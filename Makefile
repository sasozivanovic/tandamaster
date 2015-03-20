_trim.so: trim.i trim.c
	swig -python trim.i
	gcc -c -fPIC trim.c trim_wrap.c -I/usr/include/python3.4m -I/usr/include/libmp3splt
	gcc -shared trim.o trim_wrap.o  -lmp3splt -o _trim.so

trim.a: trim.c
	gcc -o trim.a trim.c -I/usr/include/libmp3splt -lmp3splt

