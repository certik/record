cdef extern int run(char *filename) nogil

def capture(filename):
    with nogil:
        run(filename)
