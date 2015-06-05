# -*- coding: utf-8 -*-
"""
Created on Fri Jun  5 10:31:01 2015

@author: Felix Pfreundtner
"""

import numpy as np
from scipy.fftpack import fft, ifft
import scipy.io.wavfile
import pyaudio
import time
import math
import ntpath

class DspOut:
    def __init__(self, gui_dict_init, fft_blocksize):
        self.binaural_block_dict = dict.fromkeys(gui_dict_init, np.zeros((fft_blocksize, 2)))
        self.binaural_dict = dict.fromkeys(gui_dict_init, np.zeros((fft_blocksize, 2)))



    # @author: Felix Pfreundtner
    def fft_convolve(self, sp_block_sp, hrtf_block_sp_l_r, fft_blocksize):

        # Do for speaker sp zeropadding: zeropad hrtf (left or right input) and speaker (mono input)
        hrtf_zeros = np.zeros((fft_blocksize-len(hrtf_block_sp_l_r), ), dtype = 'int16')
        hrtf_block_sp_zeropadded = np.concatenate((hrtf_block_sp_l_r, hrtf_zeros))
        sp_zeros = np.zeros((fft_blocksize-len(sp_block_sp), ), dtype = 'int16')
        sp_block_sp_zeropadded = np.concatenate((sp_block_sp, sp_zeros))

        # bring time domain input to to frequency domain
        hrtf_block_sp_frequency = fft(hrtf_block_sp_zeropadded, fft_blocksize)
        sp_block_sp_frequency = fft(sp_block_sp_zeropadded, fft_blocksize)

        # execute convulotion of speaker input and hrtf input: multiply complex frequency domain vectors
        binaural_block_sp_frequency = sp_block_sp_frequency * hrtf_block_sp_frequency

        # bring multiplied spectrum back to time domain, disneglected small complex time parts resulting from numerical fft approach
        binaural_block_sp = ifft(binaural_block_sp_frequency, fft_blocksize).real

        return binaural_block_sp


    # @author: Felix Pfreundtner
    def apply_hamming_window(self, inputsignal):
        hamming_window = [0.53836 - 0.46164*math.cos(2*math.pi*t/(len(inputsignal) - 1)) for t in range(len(inputsignal))]
        hamming_window = np.asarray(hamming_window, dtype=np.float64)
        inputsignal = inputsignal * hamming_window
        return inputsignal



    # @author: Felix Pfreundtner
    def bit_int(self, binaural_dict):
        binaural_dict_scaled={}
        for sp in binaural_dict:
            binaural_dict_scaled[sp] = np.zeros((len(binaural_dict[sp]), 2), dtype=np.int16)
            for l_r in range(2):
                maximum_value=np.max(np.abs(binaural_dict[sp][:, l_r]))
                if maximum_value != 0:
                    binaural_dict_scaled[sp][:, l_r] = binaural_dict[sp][:, l_r]/maximum_value * 32767
                    binaural_dict_scaled[sp] = binaural_dict_scaled[sp].astype(np.int16, copy=False)

        return binaural_dict_scaled

    # @author: Felix Pfreundtner
    def add_to_binaural_dict(self, binaural_block_dict, binaural_dict, begin_block, outputsignal_sample_number):
        outputsignal_sample_number= len(binaural_dict)
        binaural_dict[begin_block : outputsignal_sample_number, :] += binaural_block_dict[0 : (outputsignal_sample_number - begin_block), :]
        binaural_dict=np.concatenate((binaural_dict, binaural_block_dict[(outputsignal_sample_number - begin_block):, :]))
        outputsignal_sample_number= len(binaural_dict)

        return binaural_dict, outputsignal_sample_number

    # @author: Felix Pfreundtner
    def writebinauraloutput(self, binaural_dict_scaled, wave_param_common, gui_dict):
        for sp in binaural_dict_scaled:
            scipy.io.wavfile.write("./audio_out/binaural" + ntpath.basename(gui_dict[sp][2]), wave_param_common[0], binaural_dict_scaled[sp])


    # @author: Felix Pfreundtner
    def audiocallback(in_data, frame_count, time_info, flag):
        if flag:
            print("Playback Error: %i" % flag)
        if frame_count>1:
            nextiteration = pyaudio.paContinue
        else:
            nextiteration = pyaudio.paComplete
        return binaural_block_dict, nextiteration

    # @author: Felix Pfreundtner
    def startaudio(self, channels, samplerate,fft_blocksize):
        pa = pyaudio.PyAudio()
        audiostream = pa.open(format = pyaudio.paInt16,
                     channels = channels,
                     rate  = samplerate,
                     output = True,
                     frames_per_buffer = fft_blocksize,
                     stream_callback = audiocallback)

        audiostream.start_stream()
        while audiostream.is_active():
            time.sleep(0.1)
        audiostream.stop_stream()
        audiostream.close()
        pa.terminate()



