from PIL import Image
from cPickle import load

f = open("data")
data = load(f)
img_width, img_height, stride = data
print img_width, img_height, stride
i = 0
while 1:
    try:
        n = load(f)
    except EOFError:
        break
    pixels = f.read(n)
    img = Image.frombuffer("RGB", (img_width, img_height),
            pixels, "raw", "RGB", stride, 1)
    img.save("screen%04d.png" % i)
    print i
    i += 1
print "done"
print "encode by:"
print "mencoder mf://*.png -mf fps=25 -ovc lavc -lavcopts vcodec=mpeg4:vbitrate=800 -o v.avi"
