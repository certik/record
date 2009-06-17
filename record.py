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
from subprocess import Popen, PIPE, check_call, STDOUT
from tempfile import mkdtemp
from select import select

import gst

from optparse import OptionParser

class Audio(object):

    def __init__(self, filename):
        self._pipe = gst.parse_launch("""alsasrc ! audioconvert ! flacenc !  filesink location=%s""" % filename)
        self._pipe.set_state(gst.STATE_PLAYING)

    def stop(self):
        self._pipe.set_state(gst.STATE_NULL)

class Video(object):

    def __init__(self, filename, win_id=None):
        """
        Starts capturing the video and saves it to a file 'filename'.

        win_id ... the window id to capture, if None, it automatically runs
                xwininfo and parses the output to capture the windows id
        """
        if win_id is None:
            win_id = self.get_window_id()
        x, y, w, h = self.get_window_pos(win_id)
        self._pipe = Popen(["/usr/bin/recordmydesktop", "--no-sound",
            #"-windowid", "%s" % win_id,
            "-x", str(x),
            "-y", str(y),
            "-width", str(w),
            "-height", str(h),
            "-o", "%s" % filename],
            stdin=PIPE, stdout=PIPE, stderr=STDOUT)
        #p.communicate()

    def __del__(self):
        if self._pipe.poll() is None:
            self._pipe.kill()

    def stop(self):
        self._pipe.terminate()

    def flush(self):
        if select([self._pipe.stdout], [], [], 0)[0]:
            a = ""
            while select([self._pipe.stdout], [], [], 0)[0]:
                a += self._pipe.stdout.read(1)

    def wait(self):
        out = self._pipe.communicate()[0]
        if out.find("Done!!!\nGoodbye!\n") < 0:
            raise Exception("recordmydesktop failed")

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
            while 1:
                sleep(0.1)
                v.flush()
        except KeyboardInterrupt:
            pass
    finally:
        v.stop()
        a.stop()
    print "saving video"
    v.wait()
    print "done, see the work dir:", tmp_dir
    #encode(audio_file, video_file, options.filename)
    #print "output saved to:", options.filename
