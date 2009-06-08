#! /usr/bin/env python

import sys
import os
from time import sleep
from subprocess import Popen, PIPE, check_call
from tempfile import mkdtemp

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
        self._pipe = Popen(["/usr/bin/recordmydesktop", "--no-sound",
            "-windowid", "%s" % win_id, "-o", "%s" % filename],
            stdin=PIPE, stdout=PIPE, stderr=PIPE)
        #p.communicate()

    def __del__(self):
        if self._pipe.poll() is None:
            self._pipe.kill()

    def stop(self):
        self._pipe.terminate()

    def wait(self):
        #self._pipe.wait()
        self._pipe.communicate()

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
        "lavc", video, "-o", output])

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-f", "--file", dest="filename", default="out.avi",
            help="save to FILE [default: %default]", metavar="FILE")
    #parser.add_option("-w", "--window", dest="window", action="store_true"
    #        help="ask which window to capture", default=True)
    options, args = parser.parse_args()

    tmp_dir = mkdtemp()
    video_file = os.path.join(tmp_dir, "video.ogv")
    audio_file = os.path.join(tmp_dir, "audio.flac")
    print "work dir:", tmp_dir
    print "select a window to capture"
    v = Video(video_file)
    a = Audio(audio_file)
    print "press CTRL-C to stop"
    try:
        try:
            while 1:
                sleep(0.1)
                v._pipe.stdout.flush()
                v._pipe.stderr.flush()
        except KeyboardInterrupt:
            pass
    finally:
        v.stop()
        a.stop()
    print "saving video"
    v.wait()
    print "encoding"
    encode(audio_file, video_file, options.filename)
    print "output saved to:", options.filename
