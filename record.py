#! /usr/bin/env python

import sys
from time import sleep
from subprocess import Popen, PIPE

import gst

from optparse import OptionParser

class Audio(object):

    def __init__(self, filename):
        self._pipeline = gst.parse_launch("""alsasrc ! audioconvert ! flacenc !  filesink location=%s""" % filename)
        self._pipeline.set_state(gst.STATE_PLAYING)
        print "recording to '%s'" % filename

    def stop(self):
        self._pipeline.set_state(gst.STATE_NULL)
        print "waiting 1s so that gstreamer finishes saving the file..."
        sleep(1)
        print "  done."

def get_window_id():
    p = Popen("xwininfo", stdout=PIPE)
    out = p.communicate()[0]
    if p.returncode != 0:
        raise Exception("xwininfo failed")
    s = "Window id: "
    i1 = out.find(s) + len(s)
    i2 = out.find(" ", i1)
    id = out[i1: i2]
    return id

class Video(object):

    def __init__(self, win_id):
        self._pipe = Popen(["/usr/bin/recordmydesktop", "--no-sound",
            "-windowid", "%s" % win_id], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        #p.communicate()

    def stop(self):
        self._pipe.terminate()

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-f", "--file", dest="filename", default="out.flac",
            help="save to FILE [default: %default]", metavar="FILE")
    #parser.add_option("-w", "--window", dest="window", action="store_true"
    #        help="ask which window to capture", default=True)
    options, args = parser.parse_args()

    print "select a window to capture"
    win_id = get_window_id()
    a = Audio(options.filename)
    v = Video(win_id)
    print "press CTRL-C to stop"
    try:
        try:
            while 1:
                pass
        except KeyboardInterrupt:
            pass
    finally:
        v.stop()
        a.stop()
