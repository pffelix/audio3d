# -*- coding: utf-8 -*-
"""
Created on Thu Jun  4 22:06:19 2015

@author: Felix Pfreundtner
"""

import pyaudio 
import time
import scipy.io.wavfile
import threading


fs, data= scipy.io.wavfile.read("./audio/electrical_guitar_(44.1,16).wav")

counter=0
channels=1
samplerate=44100
fft_size=1024

def audiocallback(in_data, frame_count, time_info, flag):
    if flag:
        print("Playback Error: %i" % flag)
    global counter
    counter+=1
    print (counter)
    #played_frames = counter
    #pyaudio.counter += frame_count
    if counter <4:
        nextiteration = pyaudio.paContinue 
    else:
        nextiteration = pyaudio.paComplete 
    return data[0:1024], nextiteration
    
def startaudio(channels, samplerate,fft_size):    
    pa = pyaudio.PyAudio()
    audiostream = pa.open(format = pyaudio.paInt16, 
                 channels = channels,
                 rate  = samplerate,
                 output = True,
                 frames_per_buffer = fft_size,
                 stream_callback = audiocallback)
    
    audiostream.start_stream()
    while audiostream.is_active():
        time.sleep(0.1)
    audiostream.stop_stream()
    audiostream.close()
    pa.terminate()
    print()

audioutput = threading.Thread(target=startaudio(channels, samplerate, fft_size))
audioutput.start()
print ("sadg")
