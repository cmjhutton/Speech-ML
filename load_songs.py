# -*- coding: utf-8 -*-
"""
-Naim Sen-
Adapted from A. Clarke:
https://github.com/informationcake/music-machine-learning
Jun 18
"""

import librosa.display
import librosa as lb
import os
import numpy as np
import pickle
import matplotlib.pyplot as plt
import time
import multiprocessing
import itertools
import sys
from collections import OrderedDict
from more_itertools import unique_everseen
from scipy.stats import skew
from scipy.stats import kurtosis

# This python script will load in songs and extract features from the waveform.
# It will then create a dictionary of all the results, ready for plotting in
# another script. At the top we have a load of functions pre-defined, skip down
# to __main__ to see the steps we run

# a function to split up a song into TIME chunks


def splitT(mint, maxt, songdat):
    splittime = []
    for i in range(mint, maxt):
        # first axis is freq, second axis is time.
        splittime.append(songdat[:, i])
    # Return all freq for specific time range.
    return (np.array(splittime))

# a function to split up a song into FREQ chunks


def splitF(minv, maxv, songdat):
    splitfreq = []
    for i in range(minv, maxv):
        # first axis is freq, second axis is time.
        # Return all time for specific freq range.
        splitfreq.append(songdat[i, :])
    return (np.array(splitfreq))


# a function to apply the function "func" to chunks of time series data of a specified
# width in seconds.
# Returns func(chunk) for each chunk.
def compute_on_chunks(func, chunk_size, y=None, S=None, sr=22050, hop_length=512, n_fft=2048):
    # check for time series vs spectrum
    if y is not None:
        chunk_size = lb.core.time_to_samples(chunk_size, sr)
        time_series = y
    elif S is not None:
        chunk_size = lb.core.time_to_frames(chunk_size, sr=sr, hop_length=hop_length, n_fft=n_fft)
        time_series = S
    else:
        raise ValueError("compute_on_chunks() : no y or S inputted.")
    num_chunks = np.floor_divide(len(time_series), chunk_size)
    # loop over chunks and compute RMS, package into an array
    res = []
    for i in range(num_chunks):
        chunk = time_series[i*chunk_size: (i+1)*chunk_size]
        res.append(func(chunk))

    return res



# This is the main function which gets features from the songs. Most values
# returned are the mean of the whole time series, hence '_a'.
def get_features_mean(song, sr, hop_length, n_fft):
    try:
        print('extracting features...')
        # split song into harmonic and percussive parts
        y_harmonic, y_percussive = lb.effects.hpss(song)
        # Compute power spectrogram.
        stft_harmonic = lb.core.stft(
            y_harmonic, n_fft=n_fft, hop_length=hop_length)
        # Compute power spectrogram.
        stft_percussive = lb.core.stft(
            y_percussive, n_fft=n_fft, hop_length=hop_length)
        # Compute power spectrogram.
        stft_all=lb.core.stft(song, n_fft=n_fft, hop_length=hop_length)

        # =========Split by frequency bands and compute RMSE features============
        # [5,25] Choose number of bands, do low and high resolution?
        band_resolution = [12, 40]
        bands_dict = OrderedDict()
        for no_bands in band_resolution:
            # note that as n_fft is 2050 (I've decided this is sensible resolution), bands/10=freq
            bands = np.logspace(1.7, 3, no_bands) / 10
            bands_int = bands.astype(int)
            # removing double entries less than 100Hz, because logspace bunches up
            # down there and we don't need doubles when rounding to the nearest 10 Hz.
            bands_int_unique = list(unique_everseen(bands_int))
            for i in range(0, len(bands_int_unique) - 1):

                w = lb.feature.rmse(
                    S=(splitF(bands_int_unique[i], bands_int_unique[i + 1], stft_all)))
        
                # Calculate statistics over the time series.
                rms_w = np.mean(np.abs(w))
                std_w = np.std(np.abs(w))
                # skew of the time series (avg along freq axis, axis=0)
                skew_w = skew(np.mean(np.abs(w), axis=0))
                # kurtosis of time series (avg along freq axis=0)
                kurtosis_w = kurtosis(
                    np.mean(np.abs(w), axis=0), fisher=True, bias=True)
                
                # Append results to dict, with numbers as band labels
                bands_dict.update({'{0}band_rms_w{1}'.format(
                    no_bands, i): rms_w})
                bands_dict.update({'{0}band_std_w{1}'.format(
                    no_bands, i): std_w})
                bands_dict.update({'{0}band_skew_w{1}'.format(
                    no_bands, i): skew_w})
                bands_dict.update({'{0}band_kurtosis_w{1}'.format(
                    no_bands, i): kurtosis_w})

        # Compute a chromagram from a waveform or power spectrogram.
        # stft=lb.feature.chroma_stft(song, sr, n_fft=n_fft, hop_length=hop_length)
        # stft_a=np.mean(stft[0])
        # stft_std=np.std(stft[0])
        # Compute root-mean-square (RMS) energy for each frame, either from the
        # audio samples y or from a spectrogram S.
        # rmse=lb.feature.rmse(y=song)
        # rmse_a=np.mean(rmse)
        # rmse_std=np.std(rmse)

        # Compute root-mean-square (RMS) energy for harmonic
        rmseW = np.abs(lb.feature.rmse(S=stft_all))
        rmseW_a = np.mean(rmseW)
        rmseW_std = np.std(rmseW)
        rmseW_skew = skew(np.mean(rmseW, axis=0))
        rmseW_kurtosis = kurtosis(np.mean(rmseW, axis=0), fisher=True, bias=True)
        
        print('rmse features extracted')


        # ========================Whole-song spectral features===================
        # Declare dictionary
        features_dict = OrderedDict()
        # Compute the spectral centroid.
        centroid = lb.feature.spectral_centroid(
            song, sr, n_fft=n_fft, hop_length=hop_length)
        centroid_a = np.mean(centroid)
        centroid_std = np.std(centroid)
        # Compute pth-order spectral bandwidth:
        bw = lb.feature.spectral_bandwidth(
            song, sr, n_fft=n_fft, hop_length=hop_length)
        bw_a = np.mean(bw)
        bw_std = np.std(bw)
        # Compute spectral contrast [R16]
        contrast = lb.feature.spectral_contrast(
            song, sr, n_fft=n_fft, hop_length=hop_length)
        contrast_a = np.mean(contrast)
        contrast_std = np.std(contrast)
        # Get coefficients of fitting an nth-order polynomial to the columns of a spectrogram.
        polyfeat = lb.feature.poly_features(
            y_harmonic, sr, n_fft=n_fft, hop_length=hop_length)
        polyfeat_grad_a = np.mean(polyfeat[0])
        polyfeat_grad_std = np.std(polyfeat[0])
        polyfeat_const_a = np.mean(polyfeat[1])
        polyfeat_const_std = np.std(polyfeat[1])
        # zero crossing rate
        zcr = lb.feature.zero_crossing_rate(song, sr, hop_length=hop_length)
        zcr_a = np.mean(zcr)
        zcr_std = np.std(zcr)
        # onset
        onset_env = lb.onset.onset_strength(y_percussive, sr=sr)
        onset_a = np.mean(onset_env)
        onset_std = np.std(onset_env)
        print('whole song features extracted')

        # Beat sync stuff
        D = librosa.stft(song)
        # not returned, but could be if you want to plot things as a time series
        times = librosa.frames_to_time(np.arange(D.shape[1]))
        bpm, beats = lb.beat.beat_track(
            y=y_percussive, sr=sr, onset_envelope=onset_env, units='time')
        beats_a = np.mean(beats)
        beats_std = np.std(beats)
        print('beat features extracted')

        # Add features to dictionary
        features_dict.update({
            'rmseW_a': rmseW_a,
            'rmseW_std': rmseW_std,
            'centroid_a': centroid_a,
            'centroid_std': centroid_std,
            'bw_a': bw_a, 'bw_std': bw_std,
            'contrast_a': contrast_a,
            'contrast_std': contrast_std,
            'polyfeat_grad_a': polyfeat_grad_a,
            'polyfeat_grad_std': polyfeat_grad_std,
            'polyfeat_grad_a': polyfeat_grad_a,
            'polyfeat_grad_std': polyfeat_grad_std,
            'polyfeat_const_a': polyfeat_const_a,
            'polyfeat_const_std': polyfeat_const_std,
            'zcr_a': zcr_a,
            'zcr_std': zcr_std,
            'onset_a': onset_a,
            'onset_std': onset_std,
            'bpm': bpm,
            'rmseW_skew': rmseW_skew,
            'rmseW_kurtosis': rmseW_kurtosis
        })
        print('whole song features added to dictionary')
        
        # ==========================Chromatic Features===========================
        # Compute beat-synced chromagram
        chroma = lb.feature.chroma_cqt(y=song, sr=sr)
        fixed_beat = lb.util.fix_frames(beats, x_max=chroma.shape[1])
        chroma_synced = lb.util.sync(chroma, fixed_beat, aggregate=np.median)
        # compute average note weight
        # notes are labelled using the duodecimal convention t=10, e=11
        features_dict.update({
            'avg_note_weight_0': np.mean(chroma_synced[0, :]),
            'avg_note_weight_1': np.mean(chroma_synced[1, :]),
            'avg_note_weight_2': np.mean(chroma_synced[2, :]),
            'avg_note_weight_3': np.mean(chroma_synced[3, :]),
            'avg_note_weight_4': np.mean(chroma_synced[4, :]),
            'avg_note_weight_5': np.mean(chroma_synced[5, :]),
            'avg_note_weight_6': np.mean(chroma_synced[6, :]),
            'avg_note_weight_7': np.mean(chroma_synced[7, :]),
            'avg_note_weight_8': np.mean(chroma_synced[8, :]),
            'avg_note_weight_9': np.mean(chroma_synced[9, :]),
            'avg_note_weight_t': np.mean(chroma_synced[10, :]),
            'avg_note_weight_e': np.mean(chroma_synced[11, :])
        })
        # std note weight
        features_dict.update({
            'std_note_weight_0': np.std(chroma_synced[0, :]),
            'std_note_weight_1': np.std(chroma_synced[1, :]),
            'std_note_weight_2': np.std(chroma_synced[2, :]),
            'std_note_weight_3': np.std(chroma_synced[3, :]),
            'std_note_weight_4': np.std(chroma_synced[4, :]),
            'std_note_weight_5': np.std(chroma_synced[5, :]),
            'std_note_weight_6': np.std(chroma_synced[6, :]),
            'std_note_weight_7': np.std(chroma_synced[7, :]),
            'std_note_weight_8': np.std(chroma_synced[8, :]),
            'std_note_weight_9': np.std(chroma_synced[9, :]),
            'std_note_weight_t': np.std(chroma_synced[10, :]),
            'std_note_weight_e': np.std(chroma_synced[11, :])
        })

        # Tonnetz rework - instead of just taking mean and stdev, we take the
        # mean of each tonnetz dimension to give an average tonnetz position.
        # Tonnetz dims are given in the librosa docs
        tonnetz = lb.feature.tonnetz(y=song, sr=sr)
        for dim in range(tonnetz.shape[0]):
            features_dict.update({
                'avg_tonnetz_{0}'.format(dim): np.mean(tonnetz[dim, :]),
                'std_tonnetz_{0}'.format(dim): np.std(tonnetz[dim, :])
            })
        print('chromatic features added to dictionary')
        
                
        combine_features = {**features_dict, **bands_dict}


        print('features extracted successfully')
        return combine_features
    # Catch fails
    except Exception as ex:
        print('.'*20+'FAILED'+'.'*20)
        print(ex)
        print('.'*46)


# load music function, accepts any format i've encountered: mp3,wav,wma bla bla
def load_music(songname1, songpath1):
    try:
        print('loading the song: {0} ......... located here: {1} '.format(
            songname1, songpath1))
        # librosa library used to grab songdata and sample rate
        songdata1, sr1 = lb.load(songpath1)
        length=len(songdata1)
        print('done........ ' + songname1)
        return [songname1, songdata1, sr1]
    except Exception as ex:
        # the song could be corrupt? you could be trying to load
        # something which isn't a song?
        print('..............................FAILED...............................')
        print(songpath1)
        print('...................................................................')

# functions for saving/loading the python dictionaries to disk


def save_obj(obj, name):
    with open(name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)


def load_obj(name):
    with open(name + '.pkl', 'rb') as f:
        return pickle.load(f)

# If you want a grid-plot to test anything out, this will help. Although I've
# made sure get_features returns only averaged values, not time-series data, so meh.


def gridplot(data_dict, feature, size, N, ind):
    f, axarr = plt.subplots(size, size, sharey=True)
    i = 0
    j = 0
    for key in data_dict:
        # print (i,j)
        axarr[i, j].plot(np.convolve(data_dict[key][feature]
                                     [ind], np.ones((N,)) / N, mode='valid'))
        axarr[i, j].set_title(key[:3])
        if j == size - 1:
            i += 1
        j = 0 if j == size - 1 else j + 1
    for i in range(1, size, 1):
        plt.setp([a.get_yticklabels() for a in axarr[:, i]], visible=False)
    plt.savefig('test.png')


# OK so here we go...


if __name__ == "__main__":
    start_load = time.time()  # we're going to want know how long this takes...
    # if we don't use multiple cores we may as well give up now.
    # This is how many your computer has.
    num_workers = multiprocessing.cpu_count()
    print('you have {0} cores available to do your bidding...'.format(
        num_workers))
    # important parameter here; this is the size of the fft window.
    # These are sensible values
    n_fft1 = 2050
    # n_fft/5 is a sensisble value. too large and you don't sample properly.
    hop_length1 = 441

    # create song database, songdb:
    songname_tmp = []
    songpath_tmp = []
    ###load_path_root = '/raid/scratch/chutton/...'
    load_path_root = '/raid/scratch/chutton/cutting/clips/'
    load_filename = sys.argv[1]   # take command line arg for filename
    path = load_path_root + load_filename + '/'
    print(path)
    # it's saved with the same folder name but with _data.pkl on the end.
    savefile = path + load_filename + '_data'
    # now load song data in
    for song in os.listdir(path):
        # print (song)
        songname_tmp.append(song)
        songpath_tmp.append(path + '/' + song)

    # print(songname)
    # i'm just reassigning the name incase of tests with commented out lines...
    songname = songname_tmp
    songpath = songpath_tmp
    # if you want to test this on a small number of songs first (e.g. 32),
    # replace previous two lines with the following:
    # songname=songname_tmp[:31] #remember indices starts at zero.
    # songname=songname_tmp[:31]

    print('loading songs...')
    # Here we go with multi-processing, loading all our song data in
    with multiprocessing.Pool(processes=num_workers) as pool:
        # a starmap is a way to pass multiple arguments to a function using multi-process
        songdb = pool.starmap(load_music, zip(songname, songpath))
        pool.close()
        pool.join()
    print('finished loading songs into songdb')
    # print (songdb)
    print('loaded {0} songs into memory'.format(len(songdb)))
    # remove entries where loading may have failed for any reason (rare cases)
    songdb = [x for x in songdb if x is not None]
    # parse song data to individual lists ready for feature extraction function
    # (because we can't slice nested lists)
    song_name = []  # text
    song_data = []  # list of numbers
    song_sr = []  # sample rate
    for song1 in songdb:
        song_name.append(song1[0])
        song_data.append(song1[1])
        song_sr.append(song1[2])

    start_feat = time.time()  # note the time
    print("Data is all ready, now extracting features from the songs...")
    # extract features from songs with multiprocesssing
    with multiprocessing.Pool(processes=num_workers, maxtasksperchild=1) as pool:
        res = pool.starmap(get_features_mean, zip(song_data, song_sr,
                                                  itertools.repeat(hop_length1),
                                                  itertools.repeat(n_fft1)))
        pool.close()
        pool.join()

    # concatenate each songs features (res) into dictionary
    print('concatenating results into a massive dictionary...')
    data_dict_mean = {}
    for i in range(0, len(songdb)):
        data_dict_mean.update({song_name[i]: res[i]})

    # print features to screen to check
    print('{0} features were extracted. They are: '.format(len(res[0])))
    print(res[0].keys())
    print('saving dictionary to disk...')
    save_obj(data_dict_mean, savefile)
    end_feat = time.time()  # note finish time
    print("loading time: {0} seconds".format(start_feat - start_load))
    print("feature extraction time: {0} seconds".format(end_feat - start_feat))
    print("total time: {0} seconds".format(end_feat - start_load))
    print('finished')
