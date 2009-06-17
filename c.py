from PIL import Image
from cPickle import load

f = open("data")
data = load(f)
img_width, img_height, stride, fps = data
print img_width, img_height, stride, fps
i = 0
while 1:
    try:
        frame_headers = load(f)
    except EOFError:
        break
    n, skip = frame_headers
    for j in range(skip):
        # ideally this should be interpolated with the next image
        img.save("screen%04d.png" % i)
        i += 1
    pixels = f.read(n)
    img = Image.frombuffer("RGB", (img_width, img_height),
            pixels, "raw", "RGB", stride, 1)
    img.save("screen%04d.png" % i)
    print i
    i += 1
print "done"
print "encode by:"
print "mencoder mf://*.png -mf fps=%d -ovc lavc -lavcopts vcodec=mpeg4:vbitrate=800 -o v.avi" % fps
print "or by:"
print "ffmpeg2theora -F %d -v 10 screen%%04d.png -o v.ogv" % fps
