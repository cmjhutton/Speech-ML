import numpy as np
import itertools
import pickle
from sklearn import svm
from sklearn.svm import SVC
from sklearn.feature_selection import SelectFromModel
from sklearn.svm import LinearSVC
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.feature_selection import SelectFromModel
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.metrics import roc_auc_score, roc_curve, auc
from sklearn.metrics import classification_report
from sklearn.metrics import log_loss
import sklearn
from sklearn.model_selection import cross_validate
from sklearn import preprocessing
from sklearn.metrics import confusion_matrix
import os
import sys
import glob
import datetime
import matplotlib
import matplotlib.cm as cm
import matplotlib.pyplot as plt
from textwrap import wrap
import scipy.stats as stats
from scipy import interp

# This python script will take pre-made python dictionaries with feature information about an artists songs, and do machine learning and data visualisation. When I load in songs and extract features in the other script, the data is stored in a nested dictinoary structure.

# function to load in data from load_songs script.


def load_obj(name):
    with open(name + '.pkl', 'rb') as f:
        return pickle.load(f)


def prepare_data(all_data_in, data_path):
    all_features = []
    all_genders = []
    for gender in all_data_in:  # As i did feature extraction on each gender seperately, loop through them. Create lists of song names and features
        data = load_obj(gender.replace('.pkl', ''))
        print('loading {0}'.format(gender))
        videoname = []  # will be a list of videos
        videofeat = []  # will be a list of dictionaries containing the video feature data
        # will be a list of genders, as I load them gender at a time should be straightforward.
        genders = []
        for video in data:  # data is a dictionary, keys are videos
            # data corresponding to each dictionary key is another dict with features and labels
            videofeat.append(data[video])
            videoname.append(video)
            genders.append(gender.replace('_data.pkl', '').replace('all_', '').replace(
                data_path, '').replace('_data_testsplit.pkl', '').replace('_data_trainsplit.pkl', ''))
            #######################################################
            nan_keys = dict()
            items = data[video].items()
            for elem in items:
                if elem[1] is None or np.isnan(elem[1]) or np.isinf(elem[1]):
                    nan_keys.update({elem[0]: elem[1]})
            if nan_keys:
                print(video)
                print(nan_keys)

            #######################################################
        
        feature_names = list(
            videofeat[0].keys())  # will be all our feature names
        features = []  # will be all our raw feature data
        for i in range(len(videofeat)):
            # take the videofeat dictionary and grab only the values
            # (keys are just text labels for each feature)
            features.append(list(videofeat[i].values()))
        
        # create master lists of features and genders for the machine learning later
        all_features += features
        all_genders += genders 
    print(len(feature_names))
    return all_features, all_genders, feature_names


"""
We want to produce a chart showing the mean prediction probabilities
for each class. This function plots a confusion-matrix-like chart by
averaging over all samples in the class, the probabilities of the sample
being a member of each class according to the Random Forest.
"""
def plot_probability_matrix(test_data, predicted_data, figure=None, subplot_indices=221):
    classes = np.unique(test_data)
    matrix = np.zeros(shape=(len(classes), len(classes)))
    # loop over each class
    for i in range(len(classes)):
        # locate classes in test_data and match indices to predicted_data
        class_name = classes[i]
        indices = np.where(np.asarray(test_data) == class_name)
        class_probs = predicted_data[indices]
        # average over all samples in each class and average the prediction percentage
        matrix[:, i] = np.mean(class_probs, axis=0)
    if figure is not None:
        # plot a confusion-matrix-like chart
        figure.add_subplot(subplot_indices)
        plt.imshow(matrix,
                   interpolation='nearest', cmap=plt.cm.Blues)
        plt.colorbar()
        tick_marks = np.arange(len(classes))
        plt.xticks(tick_marks, classes, rotation=45)
        plt.yticks(tick_marks, classes)
        plt.title("Probability matrix")
        fmt = '.2f'
        thresh = matrix.max() / 2.
        for i, j in itertools.product(range(matrix.shape[0]), range(matrix.shape[1])):
            plt.text(j, i, format(matrix[i, j], fmt),
                     horizontalalignment="center",
                     color="white" if matrix[i, j] > thresh else "black")
      #  plt.tight_layout()
        plt.ylabel('True label')
        plt.xlabel('Predicted label')

    return matrix
'''
#commented out all standard deviation matrices for the moment

# A function to plot the standard deviations of probabilities (see probability matrix)
# The subplot configuration defaults to this matrix overlaying the confusion matrix
# (i.e. it occupies spot 224 by default). This is done because it's nicer to have a confusion
# matrix on its own rather than 5 plots on a single figure
def plot_proba_std_matrix(test_data, predicted_data, figure=None, subplot_indices=224):
    classes = np.unique(test_data)
    matrix = np.zeros(shape=(len(classes), len(classes)))
    # loop over each class
    for i in range(len(classes)):
        # locate classes in test_data and match indices to predicted_data
        class_name = classes[i]
        indices = np.where(np.asarray(test_data) == class_name)
        class_probs = predicted_data[indices]
        # average over all samples in each class and find the std of the prediction percentage
        matrix[:, i] = np.std(class_probs, axis=0)        

    if figure is not None:
        # plot a confusion-matrix-like chart
        figure.add_subplot(subplot_indices)
        plt.imshow(matrix,
                   interpolation='nearest', cmap=plt.cm.Blues)
        plt.colorbar()
        tick_marks = np.arange(len(classes))
        plt.xticks(tick_marks, classes, rotation=45)
        plt.yticks(tick_marks, classes)
        plt.title("Matrix of standard deviations in probabilities")
        fmt = '.2f'
        thresh = matrix.max() / 2.
        for i, j in itertools.product(range(matrix.shape[0]), range(matrix.shape[1])):
            plt.text(j, i, format(matrix[i, j], fmt),
                     horizontalalignment="center",
                     color="white" if matrix[i, j] > thresh else "black")
      #  plt.tight_layout()
        plt.ylabel('True label')
        plt.xlabel('Predicted label')

    return matrix
'''

# A function to compute and plot a ROC curve. Makes use of the "roc_curve"
# function provided by sklearn.
def plot_roc_curve(test_data, predicted_data, figure=None, subplot_indices=222):
    classes = np.unique(test_data)
    n_classes = len(classes)
    # loop over classes
    fpr = dict()
    tpr = dict()

    for i in range(n_classes):
        class_name = classes[i]
        # get false-positive and true-positive rates from roc_curve for the class
        fpr[i], tpr[i], _ = roc_curve(
            test_data, predicted_data[:, i], pos_label=class_name)

    # Compute macro-average ROC curve and ROC area

    # First aggregate all false positive rates
    all_fpr = np.unique(np.concatenate([fpr[i] for i in range(n_classes)]))
    # Then interpolate all ROC curves at this points
    mean_tpr = np.zeros_like(all_fpr)
    for i in range(n_classes):
        mean_tpr += interp(all_fpr, fpr[i], tpr[i])
    # Finally average it and compute AUC
    mean_tpr /= n_classes
    # compute AUC
    roc_auc = auc(all_fpr, mean_tpr)
    print('AUC = {0}'.format(roc_auc))

    # Plot ROC (Macro)
    if figure is not None:
        figure.add_subplot(subplot_indices)
        plt.plot(all_fpr, mean_tpr,
                 label='macro-average ROC curve (area = {0:0.2f})'.format(roc_auc),
                 linewidth=4)
        plt.plot([0, 1], [0, 1], 'k--', lw=2)
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('Multi-class macro average ROC curve.')
        plt.legend(loc="lower right")
     #   plt.tight_layout()
    # return AUC just in case
    return roc_auc


# plot confusion matrix - code adapted from sklearn manual page
# This function prints and plots the confusion matrix.
# Normalization can be applied by setting `normalize=True`.
def plot_confusion_matrix(test_data, predicted_data, normalize=False, figure=None, subplot_indices=224):
    classes = np.unique(test_data)
    # compute confusion matrix
    cm = confusion_matrix(test_data, predicted_data)
    if normalize:
        cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
        print("Showing normalized confusion matrix")
    else:
        print('Showing confusion matrix, without normalization')
    # print(cm)
    if figure is not None:
        figure.add_subplot(subplot_indices)
        plt.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
        plt.title('Random Forest - Confusion matrix')
        #plt.title('Multi-layer perceptron - Confusion matrix')
        plt.colorbar()
        tick_marks = np.arange(len(classes))
        plt.xticks(tick_marks, classes, rotation=45)
        plt.yticks(tick_marks, classes)

        fmt = '.2f' if normalize else 'd'
        thresh = cm.max() / 2.
        for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
            plt.text(j, i, format(cm[i, j], fmt),
                     horizontalalignment="center",
                     color="white" if cm[i, j] > thresh else "black")

     #   plt.tight_layout()
        plt.ylabel('True label')
        plt.xlabel('Predicted label')


# A function to plot feature importances
def plot_feature_importances(importances, feature_names, std, figure=None, subplot_indices=223, title="Feature Importances"):
    indices = np.argsort(importances)[::-1]
    # get feature names
    feature_names_importanceorder = []
    for f in range(len(indices)):
        feature_names_importanceorder.append(str(feature_names[indices[f]]))

    # Plot it yo
    if figure is not None:
        figure.add_subplot(subplot_indices)
    else:
        plt.figure()

    plt.title(title)
    plt.bar(range(len(indices)), importances[indices], color='r', yerr=std[indices], align='center')
    plt.xticks(range(len(indices)), feature_names_importanceorder, rotation='vertical')
    plt.xlim([-1, len(indices)])
  #  plt.tight_layout()

    return feature_names_importanceorder


# A function to save figures to a dir. The directory is autogenerated in a specified location
# using the current date & time. Figures dict should use filename : figureobject pairs.
# Also writes "meta" string containing metadata about the learning and data, to a metadata.log
# file.
def save_figs(figures_dict, meta, path_to_dir, dir_name=None):
    if dir_name is None:
        dir_name = datetime.datetime.now().isoformat()
    path = path_to_dir + '/' + dir_name
    # check if the directory exists
    if not os.path.exists(path):
        os.makedirs(path)
    else:
        raise ValueError("Path: ", path, " already exists!")

    # loop over dict entries
    for filename, fig in figures_dict.items():
        # set filepath for saving
        filepath = path + '/' + filename
        # switch current figure
        plt.figure(fig.number)
        # The following values adjust padding etc. of the subplots.
        # These optimise the layout for a 16:9 display with the plots arranged
        # as they are in the functions provided. The easiest way to adjust these
        # is by playing around in an interactive figure window (if possible) until
        # you get the layout you want and then copying the numbers down. Sadly
        # tight_layout makes the plots far too small to be useful.
        plt.subplots_adjust(top=0.92,
                            bottom=0.20,
                            left=0.10,
                            right=0.88,
                            hspace=0.60,
                            wspace=0.30)

        plt.savefig(filepath, bbox_inches='tight')

    # save metadata
    with open(path + '/' + 'metadata.log', 'w') as f:
        f.write(meta)
    # inform the user
    print("Data written to ", path)

# Here we go, let's try some machine learning algorithms

if __name__ == '__main__':

    # Set matplotlib params
    # This changes the size of created figures. Adjust for your display if necessary
    matplotlib.rcParams['figure.figsize'] = [18, 9]
    
    # load in all data saved from the feature extraction, *.pkl. Initiate figure and select colours
    path = sys.argv[1]  # command line input is path to data
    all_data = glob.glob(path + '/*_data.pkl')  # load in as many as you want

    colors = iter(cm.Set1(np.linspace(0, 1, len(all_data))))
    #colors = iter(cm.cubehelix(np.linspace(0, 1, len(all_data))))

    # load in genders with loads of videos - may or may not be splitting videos, try except:
    # feature names is same for all runs when unpacked (saves loading in a .pkl again)
    all_features, all_genders, feature_names = prepare_data(all_data, path)
    # Split our data into a training and testing data sets
    train_percent = float(sys.argv[2])
    # Test/train split as usual on genders with many videos
    features_train, features_test, genders_train, genders_test = train_test_split(
        all_features, all_genders, train_size=train_percent, random_state=0, stratify=all_genders)

    # now data is prepared for machine learning
    try:
        if len(genders_test) == len(features_test) and len(genders_train) == len(features_train):
            None
    except:
        print('genders and features are not same length: {0} != {1}', format(
            genders_test, features_test, genders_train, features_train))
        sys.exit()

    feature_names_flatten = np.array(feature_names).flatten()
    feature_names = np.transpose(feature_names)
    # print(np.transpose(feature_names))
    # set up data as numerical classes as well as labeled string classes - some classifiers require numbered labels, not genders as strings
    X_test = np.array(features_test)
    Y_test = np.array(genders_test)
    le = preprocessing.LabelEncoder()
    le.fit(Y_test)
    Y_test_n = le.transform(Y_test)

    X_train = np.array(features_train)
    Y_train = np.array(genders_train)
    le = preprocessing.LabelEncoder()
    le.fit(Y_train)
    Y_train_n = le.transform(Y_train)

    names = np.unique(Y_test)
    print(names)
    # Now try some classifiers!

    # Set up neutral network classifier

    from sklearn.preprocessing import StandardScaler
    nn_features_train = X_train
    nn_features_test = X_test
    scaler = StandardScaler()
    # normalise data and remove mean:
    scaler.fit(features_train)
    nn_features_train = scaler.transform(nn_features_train)
    nn_features_test = scaler.transform(nn_features_test)

    from sklearn.neural_network import MLPClassifier
    # not sure how many nodes to use? loop over some values until you're sure you've maxed the accuracy- 5000 is good for this:
    for i in range(5000, 5001, 1000):
        nn = MLPClassifier(hidden_layer_sizes=(
            i, ), solver='adam', max_iter=2000)
        nn_gender_model = nn.fit(nn_features_train, genders_train)
        nn_pred = nn.predict(nn_features_test)
        # get classification report
        nn_report = ('--'*30 + '\n'
                     'MLP nn classifier with {0} hidden layers'.format(i) + '\n'
                     '{0}'.format(classification_report(genders_test, nn_pred, target_names=names)) + '\n'
                     + '--'*30 + '\n'
                     )
        print(nn_report)
        
        pkl_filename = 'nn_gender_model.pkl'
        with open(pkl_filename, 'wb') as file:
            pickle.dump(nn_gender_model, file)

       
    '''
    #we could try SVC; it's quite poor compared to random forests.
    clf = svm.SVC(class_weight='balanced')
    clf.fit(X_train, Y_train_n)
    genders_SVM_pred=clf.predict(X_test)
    print('--'*30)
    print('SVM report:')
    print(classification_report(Y_test_n, genders_SVM_pred,target_names=names))
    print('--'*30)
    '''

    # Build a forest and compute the feature importances
    n_estimators = 2000  # number of trees?
    forest = RandomForestClassifier(
        n_estimators=n_estimators, random_state=2, class_weight='balanced')
    gender_model = forest.fit(features_train, genders_train)
    genders_pred = forest.predict(features_test)
    genders_proba = forest.predict_proba(features_test)
    # we'll print this later as a comparison
    accuracy_before = (accuracy_score(genders_test, genders_pred))

    # Could check classification report
    forest_unpruned_report = ('--'*30 + '\n'
                              'Random forest before pruning:\n'
                              '{0}'.format(classification_report(genders_test, genders_pred, target_names=names)) + '\n'
                              + '--'*30 +
                              '\n'
                              )
    print(forest_unpruned_report)
    
    pkl_filename = 'gender_model.pkl'  
    with open(pkl_filename, 'wb') as file:  
        pickle.dump(gender_model, file)

    # Plots before pruning!
    fig_unpruned = plt.figure()
    plot_probability_matrix(genders_test, genders_proba, figure=fig_unpruned)
    plot_roc_curve(genders_test, genders_proba, figure=fig_unpruned)
  # plot_proba_std_matrix(genders_test, genders_proba, figure=fig_unpruned)

    # plot importances unpruned
    
    importances_unpruned = forest.feature_importances_
    std_unpruned = np.std([tree.feature_importances_ for tree in forest.estimators_], axis=0)
    indices_unpruned = np.argsort(importances_unpruned)[::-1]
    
    title_unpruned = """n_est={0}, train-test={1}%, Accuracy={2:.3f}""".format(n_estimators, train_percent*100, accuracy_before, 40)
    plot_feature_importances(importances_unpruned, feature_names, std_unpruned, figure=fig_unpruned, title=title_unpruned)

  #  cm_unpruned = plt.figure()
    plot_confusion_matrix(genders_test, genders_pred, figure=fig_unpruned)

    # you could loop over trees to find out how many before you accuracy maxes output
    '''
    #how many trees are required? loop through values to find out
    scores=[]
    for val in range(1,100,10): #set accordingly
        clf=RandomForestClassifier(n_estimators=val,class_weight='balanced')
        validated = cross_validate(clf,X,Y,cv=5,scoring=['f1_weighted'])
        scores.append(validated)

    #make a nice plot:
    for i in range(0,len(scores)):
        print(scores[i]['test_f1_weighted'])
    y=[]
    x=[]
    e=[]
    for i in range(0,len(scores)):
        x.append(i)
        y.append(np.mean(scores[i]['test_f1_weighted']))
        e.append(np.mean(np.std(scores[i]['test_f1_weighted'])))
        print(np.mean(scores[i]['test_f1_weighted']), np.std(scores[i]['test_f1_weighted']))
    plt.errorbar(x,y,e)
    plt.show()
    '''

    ##############################################################################
    # Now lets repeat using a more streamlined pipeline to first remove unimportant features, then run a classifier on remaining ones.
    # we may want to try different classifiers and feature selection processes
    # an important note is that the pipeline automatically creates new feature data after removing pruned features.

    # first choose a model to prune features, then put it in pipeline - there are many we could try
    feature_selection_threshold = 0.00005
    lsvc = LinearSVC(C=feature_selection_threshold, penalty="l1", dual=False).fit(
        features_train, genders_train)
    rfc = RandomForestClassifier(n_estimators=n_estimators, random_state=2)
    modelselect = 'rfc'  # set accordingly
    pipeline = Pipeline([
        ('feature_selection', SelectFromModel(rfc)),
        ('classification', RandomForestClassifier(
            n_estimators=n_estimators, random_state=2, class_weight='balanced'))
    ])
    # do the fit and feature selection
    pipeline.fit(features_train, genders_train)
    # check accuracy and other metrics:
    genders_important_pred = pipeline.predict(features_test)
    genders_important_proba = pipeline.predict_proba(features_test)
    accuracy_after = (accuracy_score(genders_test, genders_important_pred))

    forest_pruned_report = ('accuracy before pruning features: {0:.2f}'.format(accuracy_before) + '\n'
                            'accuracy after pruning features: {0:.2f}'.format(accuracy_after) + '\n'
                            + '--' * 30 + '\n'
                            'Random Forest report after feature pruning:\n'
                            '{0}'.format(classification_report(genders_test, genders_important_pred, target_names=names)) + '\n'
                            + '--' * 30 + '\n'
                            'Log-loss = {0}'.format(log_loss(genders_test, genders_important_proba)) + '\n'
                            )
    print(forest_pruned_report)

    # Declare a figure for plotting all subplots on plot probability matrix,
    # roc curve, and confusion matrix. (The order of subplots is established
    # inside each function that takes "fig" as an argument
    fig_pruned = plt.figure()
    plot_probability_matrix(genders_test, genders_important_proba, figure=fig_pruned)
    plot_roc_curve(genders_test, genders_important_proba, figure=fig_pruned)
  # plot_proba_std_matrix(genders_test, genders_important_proba, figure=fig_pruned)

    
    # Now make get feature importances with standard deviations
    clf = pipeline.steps[1][1]  # get classifier used
    importances_pruned = pipeline.steps[1][1].feature_importances_
    std_pruned = np.std([tree.feature_importances_ for tree in clf.estimators_], axis=0)
    indices_pruned = np.argsort(importances_pruned)[::-1]
    # Construct title
    title_long = """Features pruned by {0}. n_est={1}, train-test={2}%
    , Accuracy - before={3:.3f}, after={4:,.3f}""".format(
        modelselect, n_estimators, train_percent*100, accuracy_before, accuracy_after, 40)
    # grab the pruned feature names from plot_feature_importances, and plot the chart
    feature_names_importanceorder_pruned = plot_feature_importances(importances_pruned, feature_names, std_pruned, figure=fig_pruned, title=title_long)

    # Plot pruned confusion matrix
   # cm_pruned = plt.figure()
    plot_confusion_matrix(genders_test, genders_important_pred, figure=fig_pruned)
    
    # see which features were removed
    no_features = len(feature_names_importanceorder_pruned)
    print('Started with {0} features, now using {1}'.format(
        len(feature_names), no_features))
    print('features used were:')
    print(set(feature_names_flatten) - set(feature_names_importanceorder_pruned))

    #??? np.set_printoptions(precision=2)
    

    # plt.figure(fig_pruned.number)
    # plt.tight_layout()

    # create metadata
    meta = ('music-ML metadata.log\n'
            + '=='*50 + '\n'
            'Classes:\n{0}'.format(np.unique(genders_test)) + '\n'
            + '=='*50 + '\n'
            'Features:\n{0}'.format(feature_names) + '\n'
            + '=='*50 + '\n'
            'Classification Reports:\n\n'
            '{0}\n\n{1}\n\n{2}\n\n'.format(nn_report, forest_unpruned_report, forest_pruned_report)
            )

    # more separate figures : The feature importances are really hard to see when there are many features
    fig_unpruned_importances = plt.figure()
    plot_feature_importances(importances_unpruned, feature_names, std_unpruned,
                             figure=fig_unpruned_importances, subplot_indices=111,
                             title="Feature Importances - Unpruned")

    fig_pruned_importances = plt.figure()
    plot_feature_importances(importances_pruned, feature_names, std_pruned,
                             figure=fig_pruned_importances, subplot_indices=111,
                             title="Feature Importances - Pruned")
    # construct figures dict
    figures_dict = {'rnd_forest_unpruned_graphs': fig_unpruned,
                    #'rnd_forest_cm_unpruned': cm_unpruned,
                    'rnd_forest_pruned_graphs': fig_pruned,
                    #'rnd_forest_cm_pruned': cm_pruned,
                    'rnd_forest_unpruned_importances': fig_unpruned_importances,
                    'rnd_forest_pruned_importances': fig_pruned_importances}
    savedir = '/raid/scratch/chutton/learning/'
    # dir_name = 
    save_figs(figures_dict, meta, savedir)

    plt.show()
