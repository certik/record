#! /usr/bin/env python

"""
Amplifies a wav file.
"""

from sys import argv
import wave
import audioop

def normalize(filein, fileout):
    a = wave.open(filein)
    params = a.getparams()
    nchannels, sampwidth, framerate, nframes, comptype, compname = params
    data = a.readframes(nframes)

    if sampwidth == 1:
        max_val = 0x7f
    elif sampwidth == 2:
        max_val = 0x7fff
    elif sampwidth == 4:
        max_val == 0x7fffffff

    max = audioop.max(data, sampwidth)
    factor = float(max_val)/max
    #factor = 200
    print "amplifying by F=%f" % factor

    data = audioop.mul(data, sampwidth, factor)

    b = wave.open(fileout, "w")
    b.setparams(params)
    b.writeframes(data)

if len(argv) == 3:
    normalize(argv[1], argv[2])
else:
    print "usage: amplify.py infile outfile"
