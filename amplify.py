#! /usr/bin/env python

"""
Amplifies a wav file.
"""

from sys import argv
import wave
import audioop

def amplify(filein, fileout, factor=10):
    a = wave.open(filein)
    params = a.getparams()
    nchannels, sampwidth, framerate, nframes, comptype, compname = params
    data = a.readframes(nframes)

    data = audioop.mul(data, sampwidth, factor)

    b = wave.open(fileout, "w")
    b.setparams(params)
    b.writeframes(data)

if len(argv) == 3:
    amplify(argv[1], argv[2])
else:
    print "usage: amplify.py infile outfile"
