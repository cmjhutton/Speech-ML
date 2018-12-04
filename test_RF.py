#Chloe Hutton#
#December 2018

import sys
import pickle
import numpy as np
import time
import multiprocessing
import sklearn
from sklearn.ensemble import RandomForestClassifier

#given that learning.py has produced a trained random forest, this function takes any audio clip and decides its class - male or female                                                                          
#if a long piece of audio is cut into ~5 second slices, can assume that only one person is talking in each slice                                                                                                  
#by iterating the function over all the slices, can decide what fractions of the speakers are male and female    
def test_audio(clip):    
    #clipfeat is a array of slices; each slice contains a dictionary of features
    clipfeat = []
    for clip in data:
        clipfeat.append(data[clip])
    
    features = [] #shape is n_slices by n_features
    for i in range(0, len(clipfeat)):
        features.append(list(clipfeat[i].values()))
        
    gender_pred = forest.predict(features)
    unique, counts = np.unique(gender_pred, return_counts=True)
    print(unique)
    print(counts)
    print(len(list(clipfeat[1].values())))
    
if __name__ == '__main__':

    start_time = time.time()

    #load in forest
    model = sys.argv[1]
    forest = pickle.load(open(model, 'rb'))
    print('forest loaded in')

    #load in data
    path = sys.argv[2]
    data = pickle.load(open(path, 'rb'))
    print('data loaded in')

    test_audio(data)

    end_time = time.time()

    print('run time: {0} seconds'.format(end_time - start_time))
    print('done')
