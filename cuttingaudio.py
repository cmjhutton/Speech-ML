#Chloe Hutton#                                                                                                                                                                                                     
#December 2018                                                                                                                                                                                                     
#This program takes an audio file and slices it into n pieces of equal length, using AudioSegment and multiprocessing                                                                                              

import os
import sys
import glob
import math
import time
import multiprocessing
import pydub
from pydub import AudioSegment

start_time = time.time()

#define the directory you want to take audio from, first argument in command line                                                                                                                                  
path = sys.argv[1]
videodir = '/raid/scratch/chutton/cutting/clips/' + path
#make this the current working directory                                                                                                                                                                           
os.chdir(videodir)
#extract every file in this directory of the format you want, mp3 mp4 wav etc                                                                                                                                      
file_list = glob.glob('*.mp4')

num_workers = multiprocessing.cpu_count()
print('{0} cores available'.format(num_workers))

#function to cut an audio file into pieces of a specified length                                                                                                                                                   
def extract_audio(file):
    audio = AudioSegment.from_file(file, 'mp4')
    duration = audio.duration_seconds
    #number of slices the audio is cut into, given a rough length of a slice of n seconds - n is the second argument in the command line                                                                           
    total_slices = math.ceil(duration / sys.argv[2])
    #duration is in seconds,  AudioSegment works in milliseconds = factor of 1000                                                                                                                                  
    length_of_slice = 1000*duration/total_slices
    #for loop takes cuts of duration length_of_slice along length of whole audio and saves them all in directory in the current path called pathclips                                                              
    for i in range(0, total_slices):
        slice_i = audio[length_of_slice*i:length_of_slice*(i + 1)]
        slice_i.export('/raid/scratch/chutton/cutting/clips/' + path + '/' + path + 'clips/' + 'slice_' + str(i) + '_' + file, format = 'mp4')

#multiprocessing over the files in the directory, ~32 processed at a time                                                                                                                                          
if __name__ == '__main__':
    pool = multiprocessing.Pool(processes=num_workers)
    pool.map(extract_audio, file_list)
    pool.close()
    pool.join()

end_time = time.time()
print('run time: {0} seconds'.format(end_time - start_time))
print('done')
-UU-:**--F1  cutting.py     Top L3     (Python) -------------------------------------------------------------------------------------------------------------------------------------------------------------------

