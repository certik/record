import gtk
from time import sleep
from timeit import default_timer as clock
from PIL import Image
from cPickle import dump

def wait(fps=2):
    """
    Generates consecutive integers with the given "fps".

    It maintains the constant fps, and if necessary, it skips frames (in this
    case the "skip" variable returns the number of skipped frames).
    """
    i = 1
    t = clock()
    while 1:
        free_count = 0
        skip = 0
        while free_count == 0:
            while clock()-t < float(i)/fps:
                free_count += 1
            if free_count == 0:
                i += 1
                skip += 1
        yield i-1, skip
        i += 1


img_width = gtk.gdk.screen_width()
img_height = gtk.gdk.screen_height()
img_width = 657
img_height = 435

screengrab = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8,
    img_width, img_height)


fps = 15
f = open("data", "w")
headers = (img_width, img_height, screengrab.get_rowstride(), fps)
dump(headers, f)
t = clock()
t_start = t
for i, skip in wait(fps=fps):
    t_new = clock()
    screengrab.get_from_drawable(gtk.gdk.get_default_root_window(),
        gtk.gdk.colormap_get_system(), 0, 0, 0, 0, img_width, img_height)
    img = screengrab.get_pixels()
    frame_header = (len(img), skip)
    dump(frame_header, f)
    f.write(img)
    i += 1
    print "time: %.3f, frame: %04d, current fps: %6.3f, skip: %d, " \
            "lag: %.6f" % ( t_new-t_start, i, 1/(t_new-t), skip,
                    t_new-t_start - float(i)/fps)
    t = t_new
