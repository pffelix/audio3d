# -*- coding: utf-8 -*-
"""
Module to read / write wav files using numpy arrays
Functions
---------
`read`: Return the sample rate (in samples/sec) and data from a WAV file.
`write`: Write a numpy array as a WAV file.
"""
from __future__ import division, print_function, absolute_import

import struct
import warnings


class WavFileWarning(UserWarning):
    pass

_big_endian = False

WAVE_FORMAT_PCM = 0x0001
WAVE_FORMAT_IEEE_FLOAT = 0x0003
WAVE_FORMAT_EXTENSIBLE = 0xfffe
KNOWN_WAVE_FORMATS = (WAVE_FORMAT_PCM, WAVE_FORMAT_IEEE_FLOAT)

# assumes file pointer is immediately
#  after the 'fmt ' id
#'iHHIIHH'

def _read_fmt_chunk(fid):
    print ("5")
    if _big_endian:
        fmt = '>'
    else:
        fmt = '<'
    res = struct.unpack(fmt+'iHHIIHH',fid.read(20))
    size, comp, noc, rate, sbytes, ba, bits = res
    print ("6")
    if comp not in KNOWN_WAVE_FORMATS or size > 16:
        comp = WAVE_FORMAT_PCM
        warnings.warn("Unknown wave file format", WavFileWarning)
        if size > 16:
            fid.read(size - 16)

    return size, comp, noc, rate, sbytes, ba, bits


def _skip_unknown_chunk(fid):
    if _big_endian:
        fmt = '>i'
    else:
        fmt = '<i'

    data = fid.read(4)
    size = struct.unpack(fmt, data)[0]
    fid.seek(size, 1)

def _read_riff_chunk(fid):
    print ("3")
    global _big_endian
    str1 = fid.read(4)
    if str1 == b'RIFX':
        _big_endian = True
    elif str1 != b'RIFF':
        raise ValueError("Not a WAV file.")
    if _big_endian:
        fmt = '>I'
    else:
        fmt = '<I'
    print ("endian:", _big_endian)
    fsize = struct.unpack(fmt, fid.read(4))[0] + 8
    str2 = fid.read(4)
    if (str2 != b'WAVE'):
        raise ValueError("Not a WAV file.")
    if str1 == b'RIFX':
        _big_endian = True
    return fsize
    
# open a wave-file


def read(filename, mmap=False):
    """
    Return the sample rate (in samples/sec) and data from a WAV file
    Parameters
    ----------
    filename : string or open file handle
        Input wav file.
    mmap : bool, optional
        Whether to read data as memory mapped.
        Only to be used on real files (Default: False)
        .. versionadded:: 0.12.0
    Returns
    -------
    rate : int
        Sample rate of wav file
    data : numpy array
        Data read from wav file
    Notes
    -----
    * The file can be an open file or a filename.
    * The returned sample rate is a Python integer
    * The data is returned as a numpy array with a
      data-type determined from the file.
    """
    i = 0
    print ("1")
    if hasattr(filename,'read'):
        fid = filename
        mmap = False
    else:
        fid = open(filename, 'rb')
        print ("fid.open first:", fid.tell())
        print ("2")
        
    try:
        fsize = _read_riff_chunk(fid) # writes no. of total bytes in fsize
        print ("fid.open 1.5:", fid.tell())
        noc = 1
        bits = 8
        comp = WAVE_FORMAT_PCM
        rate = 0
        print ("4")
        print ("fid.open 2nd:", fid.tell())
        while (fid.tell() < fsize):
            # read the next chunk
            print ("fid.tell while:", fid.tell())
            print (fsize)
            chunk_id = fid.read(4)
            print ("4.1", i+1)
            if chunk_id == b'fmt ':
                size, comp, noc, rate, sbytes, ba, bits = _read_fmt_chunk(fid)  
                print (size, comp, noc, rate, sbytes, ba, bits)
            #elif chunk_id == b'data':
                #data = _read_data_chunk(fid, comp, noc, bits, mmap=mmap)
           
            else:
                warnings.warn("Chunk (non-data) not understood, skipping it.",
                              WavFileWarning)
                _skip_unknown_chunk(fid)
    finally:
        if not hasattr(filename,'read'):
            fid.close()
        else:
            fid.seek(0)

    return rate, fsize

rateoffile, sizeoffile = read("./audio/synthesizer_(44.1,16).wav")
print (rateoffile, sizeoffile)