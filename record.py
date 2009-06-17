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
from cPickle import dump

import gst
import gtk

from optparse import OptionParser

class Audio(object):

    def __init__(self, filename):
        self._pipe = gst.parse_launch("""alsasrc ! audioconvert ! flacenc !  filesink location=%s""" % filename)
        self._pipe.set_state(gst.STATE_PLAYING)

    def stop(self):
        self._pipe.set_state(gst.STATE_NULL)

class Video(object):

    def __init__(self, filename, win_id=None, fps=15):
        """
        Starts capturing the video and saves it to a file 'filename'.

        win_id ... the window id to capture, if None, it automatically runs
                xwininfo and parses the output to capture the windows id
        """
        if win_id is None:
            win_id = self.get_window_id()
        x, y, w, h = self.get_window_pos(win_id)
        self.x = x
        self.y = y
        self.width = w
        self.height = h
        self.fps = fps
        self.screengrab = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, w, h)
        self._datafile = open("data", "w")
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
    audio_file = os.path.join(tmp_dir, "audio.flac")
    print "work dir:", tmp_dir
    print "select a window to capture"
    v = Video(video_file, options.window)
    a = Audio(audio_file)
    print "Capturing audio and video. Press CTRL-C to stop."
    try:
        try:
            v.start()
        except KeyboardInterrupt:
            pass
    finally:
        a.stop()
    print "stopped."
    print "done, see the work dir:", tmp_dir
    #encode(audio_file, video_file, options.filename)
    #print "output saved to:", options.filename
