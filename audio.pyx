cdef extern from "arecord.h":
    int run(char *filename)

def capture(filename):
    print filename
