from __future__ import print_function
import numpy as np
import matplotlib.pyplot as plt
import pylab
import librosa
import librosa.display

########################
# Load the example clip
y, sr = librosa.load('/raid/scratch/chutton/cutting/clips/ana_english/ana_english.mp4')


###############################################
# Compute the short-time Fourier transform of y
D = librosa.stft(y)

# Compute spectrogram
rp = np.max(np.abs(D))
plt.rcParams['font.family']='serif'
librosa.display.specshow(librosa.amplitude_to_db(np.abs(D), ref=rp), y_axis='log')
plt.colorbar()
pylab.savefig('/raid/scratch/chutton/learning/figures/files/ana_spectrogram.png')
plt.show()

