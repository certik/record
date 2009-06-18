all:
	gcc -c -o aplay.o aplay.c
	gcc -o arecord aplay.o -lasound
