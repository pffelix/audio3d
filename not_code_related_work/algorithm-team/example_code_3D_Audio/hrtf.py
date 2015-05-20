from numpy import *
from scipy import *
import numpy as n
import scipy.io.wavfile as wav
import scipy.signal as dsp
import pylab

def hamming_window(N):
	return lambda t : 0.53836 - 0.46164*cos(2*n.pi*t/(N - 1))
 
def read(elev, azimuth, N=128):
	""" Accepts elev and azimuth in degrees, and returns closest impulse response and transfer function to that combination from compact KEMAR HRTF measurements"""

	elev, azimuth, flip = setangles(elev, azimuth)
	

	filename = "compact/elev"+str(elev)+"/H"+str(elev)+"e"+str(azimuth)+"a.wav"
	fs, h_t = wav.read(filename)
	print (elev,azimuth)
	h_t_l = transpose(transpose(h_t)[0])
	h_t_r = transpose(transpose(h_t)[1])
	if flip:
		return h_t_r, h_t_l
	return h_t_l, h_t_r

def setangles(elev, azimuth):
	elev = int(elev)
	azimuth = int(azimuth)
	
	#bring to multiple of ten
	if elev != 0:
		while elev%10 > 0:
			elev = elev + 1

	if elev > 90:
		elev = 90
	if elev < -40:
		elev = -40

	#Set increment of azimuth based on elevation
	if abs(elev) < 30:
		incr = 5
	elif abs(elev) == 30:
		incr = 6
	elif abs(elev) == 40:
		incr = 6.43
		opts = [0, 6, 13, 19, 26, 32, 29, 45, 51, 58, 64, 71, 77, 84, 90, 96, 103, 109, 116, 122, 129, 135, 141, 148, 154, 161, 167, 174, 180]
	elif elev == 50:
		incr = 8
	elif elev == 60:
		incr = 10
	elif elev == 70:
		incr = 15
	elif elev == 80:
		incr = 30
	elif elev == 90:
		incr = 0
		azimuth = 0
	flip = False

	#bring into [-pi,pi]
	while azimuth > 180:
		azimuth = azimuth - 180
	while azimuth < -180:
		azimuth = azimuth + 180

	#check if we need to flip left and right.
	if azimuth < 0:
		azimuth = abs(azimuth)
		flip = True

	if abs(elev) == 40:
		incr = 6.43
		num = incr
		while azimuth > num:
			num = num + incr

		azimuth = str(int(round(num)))
		#special case for non-integer increment

	elif azimuth != 0:
		while azimuth % incr > 0:
			azimuth = azimuth + 1

	if int(azimuth) < 100:
		azimuth = "0" + str(int(azimuth))
		
	if int(azimuth) < 10:
		azimuth = "00"+ str(int(azimuth))

	return elev, azimuth, flip

def project(sig, elev, azimuth):
	h_t_l, h_t_r = read(elev, azimuth)

	Hw_l = fft(h_t_l, len(sig))
	Hw_r = fft(h_t_r, len(sig))

	f_diner = fft(sig)
	f_diner_l = Hw_l*f_diner
	f_diner_r = Hw_r*f_diner
	t_diner_l = ifft(f_diner_l, len(sig))
	t_diner_r = ifft(f_diner_r, len(sig))
	return t_diner_l, t_diner_r


def path(t_sig,start, end, duration=0, window_size=1024, fs=44100):
	""" Moves a sound from start to end positions over duration (Seconds)"""
	M = (fs/2.) / window_size
	w = r_[:fs/2.:M]
	N = len(w)

	window = hamming_window(N)(r_[:window_size])

	i = 1
	elev = start[0]
	elev_end = end[0]

	if duration == 0:
		duration = len(t_sig)/fs
	
	azimuth = start[1]
	azimuth_end = end[1]
	N_steps = int(len(t_sig) * 2 / window_size)
	elev_delta = float((elev_end - elev) / float(N_steps)) #deg/half-window
	azimuth_delta = float((azimuth_end - azimuth) / float(N_steps))

	output_l = zeros( len(t_sig) )
	output_r = zeros( len(t_sig) )

	while i*(window_size) < len(t_sig):
		ind_min = (i-1.)*window_size
		ind_max = (i)*window_size
		t_sig_w = t_sig[ind_min:ind_max] * window
		t_output_l, t_output_r = project(t_sig_w, elev, azimuth)
			
		output_l[ind_min:ind_max] += t_output_l
		output_r[ind_min:ind_max] += t_output_r

		elev = elev + elev_delta
		azimuth = azimuth + azimuth_delta
		
		i = i + 0.5

	return output_l, output_r

def inverse_transfer_function(Hw):
	max_Hw = max(Hw)
	
	inv_Hw = (Hw + 1./max_Hw ) ** -1
	return inv_Hw

def speaker_transform(sig_l, sig_r):
	theta_l = -30
	theta_r = 30

	ht_l_l, ht_l_r = read(0, theta_l)
	ht_r_l, ht_r_r = read(0, theta_r)

	H_l_l = fft(ht_l_l, len(sig_l))
	H_l_r = fft(ht_l_r, len(sig_l))
	H_r_l = fft(ht_r_l, len(sig_l))
	H_r_r = fft(ht_r_r, len(sig_l))

	f_sig_l = fft(sig_l, len(H_l_l))
	f_sig_r = fft(sig_r, len(H_l_l))

	C = ((H_l_l*H_r_r - H_r_l * H_l_r)**-1)

	
	f_output_l = C*H_r_r*f_sig_l - H_r_l*f_sig_r
	f_output_r = C*H_l_l*f_sig_r - H_l_r*f_sig_l

	t_output_l = ifft(f_output_l, len(sig_l))
	t_output_r = ifft(f_output_r, len(sig_r))

	return t_output_l, t_output_r

	Hw_weak_side = fft(ht_l_l, len(sig_l))
	Hw_strong_side = fft(ht_l_r, len(sig_r))

	

	f_sig_l = f_sig_l * Hw_strong_side + f_sig_r * Hw_weak_side
	f_sig_r = f_sig_l * Hw_weak_side + f_sig_r * Hw_strong_side

	t_sig_l = ifft(f_sig_l, len(sig_l))
	t_sig_r = ifft(f_sig_r, len(sig_r))

	return t_sig_l, t_sig_r

	"""
	D = 4.
	delta = 0.15
	theta = pi/4.
	g = D / (delta * sin(theta) + D)
	ht_l, ht_l = read(0, 45)
	Hw = fft(h_t_l, len(sig_l))

	A_inv = lambda z : ( 1. / (1 - g**2 * Hw**2 * z**(-2*d)) ) * array([[1,-g*Hw*z**-d],[-g*Hw*z**-d, 1]])

	(L_sig, R_sig) = multiply(A_inv(r_[:]), array([[sig_l],[sig_r]]))
	

	f_sig_l = fft(sig_l, len(sig_l))
	"""
	


fs, t_diner = wav.read('binaural_toms_diner.wav')

t_diner_l, t_diner_r = path(t_diner, (0,-180), (0, 180), 0, 44100/10., fs)
#for i in range(9):
#	angle = i*20
#t_diner_l, t_diner_r = project(t_diner, 0, angle)
wav.write('sounds/diner_360_headphone.wav', fs, n.column_stack((t_diner_l,t_diner_r)))

###t_diner_l, t_diner_r = speaker_transform(t_diner_l, t_diner_r)
###print ("Making Speaker Stereo")
###wav.write('sounds/diner_360_speaker.wav', fs, n.column_stack((t_diner_l,t_diner_r)))

t_diner_l, t_diner_r = path(t_diner, (90, 0), (-40, 0), 0, 44100/10., fs)
#for i in range(9):
#	angle = i*20
#t_diner_l, t_diner_r = project(t_diner, 0, angle)
wav.write('sounds/diner_toptobottom_headphone.wav', fs, n.column_stack((t_diner_l,t_diner_r)))

###t_diner_l, t_diner_r = speaker_transform(t_diner_l, t_diner_r)
###print ("Making Speaker Stereo")
###wav.make_stereo('sounds/diner_toptobottom_speaker.wav', t_diner_l, t_diner_r, fs)




