import gtk
from time import sleep
from timeit import default_timer as clock
from PIL import Image
from cPickle import dump

def wait(fps=2):
    """
    Generates consecutive integers with the given "fps".

    It maintains the constant fps.
    """
    i = 1
    t = clock()
    while 1:
        free_count = 0
        while clock()-t < float(i)/fps:
            free_count += 1
        yield i-1, free_count
        i += 1


img_width = gtk.gdk.screen_width()
img_height = gtk.gdk.screen_height()
img_width = 657
img_height = 435

screengrab = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8,
    img_width, img_height)


fps = 15
f = open("data", "w")
data = (img_width, img_height, screengrab.get_rowstride(), fps)
dump(data, f)
t = clock()
t_start = t
for i, count in wait(fps=fps):
    t_new = clock()
    screengrab.get_from_drawable(gtk.gdk.get_default_root_window(),
        gtk.gdk.colormap_get_system(), 0, 0, 0, 0, img_width, img_height)
    img = screengrab.get_pixels()
    dump(len(img), f)
    f.write(img)
    i += 1
    print "frame: %04d, current fps: %6.3f, free-count: %06d, time: %.3f, " \
            "lag: %.3f" % (i, 1/(t_new-t), count, t_new-t_start,
                    t_new-t_start - float(i)/fps)
    t = t_new
