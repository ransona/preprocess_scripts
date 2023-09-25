# will make matrices of summaries of trials:
# do this for dF, F, spikes
# mean ca pre and post period for each trial [cells,trials,time]
# median ca pre and post period for each trial
# max ca pre and max post period

# cycle through each experiment ID
# compose averaged values into 2d matrices
# save these in seperate dict files, each with the config used and the data

import organise_paths
import os
import numpy as np
import pickle
from pandas import read_csv

def run_trial_average_batch(trial_average_config):
    userID = trial_average_config['userID']
    expIDs = trial_average_config['expIDs']
    chs = trial_average_config['chs']
    # trial_average_config['pre_interval'] = [-0.5, 0.0] 
    # trial_average_config['post_interval'] = [0.5, 2.0]
    # trial_average_config['name'] = 'trial-0.5_0.0__0.5_2.0'

    for expID in expIDs:
        for ch in chs:
            # load calcium data
            # load eye data
            animalID, remote_repository_root, processed_root, exp_dir_processed, exp_dir_raw = organise_paths.find_paths(userID, expID)
            # load all exp data
            exp_dir_processed_recordings = os.path.join(exp_dir_processed,'recordings')
            exp_dir_processed_cut = os.path.join(exp_dir_processed,'cut')
            data = {}
            # dF
            with open(os.path.join(exp_dir_processed_cut,'s2p_ch' + str(ch) + '_dF_cut.pickle'), "rb") as file: data['s2p_dF_cut'] = pickle.load(file)
            # F
            with open(os.path.join(exp_dir_processed_cut,'s2p_ch' + str(ch) + '_F_cut.pickle'), "rb") as file: data['s2p_F_cut'] = pickle.load(file)
            # spikes
            with open(os.path.join(exp_dir_processed_cut,'s2p_ch' + str(ch) + '_Spikes_cut.pickle'), "rb") as file: data['s2p_Spikes_cut'] = pickle.load(file)
            # movement
            with open(os.path.join(exp_dir_processed_cut,'wheel.pickle'), "rb") as file: data['s2p_Spikes_cut'] = pickle.load(file)
            # eye
            with open(os.path.join(exp_dir_processed_cut,'eye_left_cut.pickle'), "rb") as file: data['eye_left'] = pickle.load(file)
            with open(os.path.join(exp_dir_processed_cut,'eye_right_cut.pickle'), "rb") as file: data['eye_right'] = pickle.load(file)
            # trial stimulus data
            data['all_trials'] = read_csv(os.path.join(exp_dir_processed, expID + '_all_trials.csv'))

            # make space for all data types
            # cycle through trials collecting all averages maxes mins etc
            # save the whole beast
