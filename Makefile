all:
	cython audio.pyx
	gcc -fPIC -I/usr/include/python2.6 -c -o audio.o audio.c
	gcc -fPIC -c -o arecord.o arecord.c
	gcc -shared -o audio.so audio.o arecord.o -lasound
