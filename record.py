#! /usr/bin/env python

"""
Captures a video of a window plus audio, then encodes this into one media file.

Other tips:

1) extracting audio from avi file:

$ mplayer -ao pcm:fast:file=audio_out.wav -vo null -vc null some_video.ogv

2) taking video from one file and audio from another:

$ mencoder -audiofile audio_out.wav -oac lavc -ovc lavc some_video.ogv \
        -o out.avi

"""

import sys
import os
import re
from time import sleep
from timeit import default_timer as clock
from subprocess import Popen, PIPE, check_call, STDOUT
from tempfile import mkdtemp
from select import select
from cPickle import dump, load
from optparse import OptionParser
from threading import Thread

import gtk
from PIL import Image

from audio import capture, capture_stop

class Audio(Thread):

    def __init__(self, filename):
        Thread.__init__(self)
        self._filename = filename

    def run(self):
        capture(self._filename)

    def stop(self):
        capture_stop()

class Video(object):

    def __init__(self, tmpdir, win_id=None, fps=15):
        """
        Starts capturing the video and saves it to a file 'filename'.

        win_id ... the window id to capture, if None, it automatically runs
                xwininfo and parses the output to capture the windows id
        """
        x, y, w, h = self.get_active_window_pos()
        self.x = x
        self.y = y
        self.width = w
        self.height = h
        self.fps = fps
        self.tmpdir = tmpdir
        self.screengrab = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, w, h)
        self._datafile = open(tmpdir+"/data", "w")
        headers = (w, h, self.screengrab.get_rowstride(), fps)
        dump(headers, self._datafile)

    def wait(self, fps=2):
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

    def start(self):
        t = clock()
        t_start = t
        for i, skip in self.wait(fps=self.fps):
            t_new = clock()
            self.screengrab.get_from_drawable(gtk.gdk.get_default_root_window(),
                    gtk.gdk.colormap_get_system(),
                    self.x, self.y, 0, 0, self.width, self.height)
            img = self.screengrab.get_pixels()
            frame_header = (len(img), skip)
            dump(frame_header, self._datafile)
            self._datafile.write(img)
            i += 1
            print "time: %.3f, frame: %04d, current fps: %6.3f, skip: %d, " \
                    "lag: %.6f" % ( t_new-t_start, i, 1/(t_new-t), skip,
                            t_new-t_start - float(i)/self.fps)
            t = t_new

    def get_window_pos(self, win_id, dX=0, dY=-17, dw=2, dh=16):
        """
        Determines the correct window position and dimensions.

        win_id ... windows ID to whose parameters are to be determined
        dX, dY, dw, dh ... those are corrections that have to be applied to
                           what is read from xwininfo

        Note: they are not precised anyways, there seems to be some weird
        rounding to multiplies of 4...
        """
        p = Popen(["xwininfo", "-id", win_id], stdout=PIPE)
        out = p.communicate()[0]
        if p.returncode != 0:
            raise Exception("xwininfo failed")
        X = int(re.search("Absolute upper-left X:.*?(\d+)", out).groups()[0])
        Y = int(re.search("Absolute upper-left Y:.*?(\d+)", out).groups()[0])
        width = int(re.search("Width:.*?(\d+)", out).groups()[0])
        height = int(re.search("Height:.*?(\d+)", out).groups()[0])
        X += dX
        Y += dY
        width += dw
        height += dh
        return X, Y, width, height

    def get_active_window_pos(self):
        root = gtk.gdk.screen_get_default()
        win = root.get_active_window()
        winw, winh = win.get_geometry()[2:4]
        _or, _ror = win.get_origin(), win.get_root_origin()
        border, titlebar = _or[0] - _ror[0], _or[1] - _ror[1]
        w, h = winw + (border*2), winh + (titlebar+border)
        x, y = win.get_root_origin()
        return x, y, w, h

    def get_window_id(self):
        p = Popen("xwininfo", stdout=PIPE)
        out = p.communicate()[0]
        if p.returncode != 0:
            raise Exception("xwininfo failed")
        s = "Window id: "
        i1 = out.find(s) + len(s)
        i2 = out.find(" ", i1)
        id = out[i1: i2]
        return id

    def convert(self):
        self._datafile.close()
        f = open(self.tmpdir+"/data")
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
                img.save(self.tmpdir + "/screen%04d.png" % i)
                i += 1
            pixels = f.read(n)
            img = Image.frombuffer("RGB", (img_width, img_height),
                    pixels, "raw", "RGB", stride, 1)
            img.save(self.tmpdir + "/screen%04d.png" % i)
            print i
            i += 1
        print "images saved to: %s" % self.tmpdir


def encode(audio, video, output):
    """
    Combines the audio and video to a resulting file.
    """
    check_call(["mencoder", "-audiofile", audio, "-oac", "lavc", "-ovc",
        "lavc", video, "-o", output], stdin=PIPE, stdout=PIPE, stderr=STDOUT)

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-f", "--file", dest="filename", default="out.avi",
            help="save to FILE [default: %default]", metavar="FILE")
    parser.add_option("-w", "--window", dest="window",
            help="window id to capture", default=None)
    options, args = parser.parse_args()

    tmp_dir = mkdtemp()
    video_file = os.path.join(tmp_dir, "video.ogv")
    audio_file = os.path.join(tmp_dir, "audio.wav")
    print "work dir:", tmp_dir
    print "select a window to capture (1s sleep)"
    sleep(1)
    print "active window selected"
    v = Video(tmp_dir, options.window)
    a = Audio(audio_file)
    print "Capturing audio and video. Press CTRL-C to stop."
    try:
        try:
            a.start()
            v.start()
        except KeyboardInterrupt:
            pass
    finally:
        a.stop()
    print "stopped."
    print "converting to png images"
    v.convert()
    print "To encode using mencoder:"
    print "-"*80
    print "mencoder mf://%s/*.png -mf fps=%d -audiofile %s -oac lavc " \
            "-ovc lavc -lavcopts vcodec=mpeg4:vbitrate=800 -o v.avi" % \
            (tmp_dir, v.fps, audio_file)
    print "-"*80
    print
    print "To encode using theora:"
    print "-"*80
    print "ffmpeg2theora -F %d -v 10 %s/screen%%04d.png -o tmp.ogv" % \
            (v.fps, tmp_dir)
    print "oggenc %s" % audio_file
    print "oggz-merge -o v.ogv tmp.ogv %sogg" % audio_file[:-3]
    print "-"*80
