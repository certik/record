import gtk
from time import sleep
from timeit import default_timer as clock
from PIL import Image
from cPickle import dump

def wait(fps=2):
    i = 0
    t = clock()
    while 1:
        while clock()-t < 1./fps:
            # sleeping here is too imprecise
            # sleep(0.001)
            pass
        t = clock()
        yield i
        i += 1


img_width = gtk.gdk.screen_width()
img_height = gtk.gdk.screen_height()
img_width = 657
img_height = 435

screengrab = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8,
    img_width, img_height)


f = open("data", "w")
data = (img_width, img_height, screengrab.get_rowstride())
dump(data, f)
fps = 15
t = clock()
for i in wait(fps=fps):
    screengrab.get_from_drawable(gtk.gdk.get_default_root_window(),
        gtk.gdk.colormap_get_system(), 0, 0, 0, 0, img_width, img_height)
    img = screengrab.get_pixels()
    #print len(img)/1024./1024
    #img = Image.frombuffer("RGB", (img_width, img_height),
    #        screengrab.get_pixels(), "raw", "RGB",
    #        screengrab.get_rowstride(), 1)
    #img.save("screen%04d.ppm" % i)
    #images.append(img)
    #dump(img, f)
    dump(len(img), f)
    f.write(img)
    #f.flush()
    i += 1
    print i, 1/(clock()-t)
    t = clock()
    #print t-t_start

#print i
#print "fps=", i/10.
#print "saving"
#for i, img in enumerate(images):
#    print i
#    img.save("screen%04d.png" % i)
