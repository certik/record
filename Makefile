all:
	gcc -c -o arecord.o arecord.c
	gcc -o arecord arecord.o -lasound
