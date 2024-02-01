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
import time

def run_trial_average_batch(trial_average_config):
    userID = trial_average_config['userID']
    expIDs = trial_average_config['expIDs']
    chs = trial_average_config['chs']

    for expID in expIDs:
        print('Starting experiment ' + expID)
        animalID, remote_repository_root, processed_root, exp_dir_processed, exp_dir_raw = organise_paths.find_paths(userID, expID)
        exp_dir_processed_recordings = os.path.join(exp_dir_processed,'recordings')
        exp_dir_processed_cut = os.path.join(exp_dir_processed,'cut')
        exp_dir_processed_trial_average = os.path.join(exp_dir_processed,'trial_average')
        os.makedirs(exp_dir_processed_trial_average, exist_ok = True)
        neural_activity = {}
        for ch in chs:
            data = {}
            # dF
            with open(os.path.join(exp_dir_processed_cut,'s2p_ch' + str(ch) + '_dF_cut.pickle'), "rb") as file: data['s2p_dF_cut'] = pickle.load(file)
            # F
            with open(os.path.join(exp_dir_processed_cut,'s2p_ch' + str(ch) + '_F_cut.pickle'), "rb") as file: data['s2p_F_cut'] = pickle.load(file)
            # spikes
            with open(os.path.join(exp_dir_processed_cut,'s2p_ch' + str(ch) + '_Spikes_cut.pickle'), "rb") as file: data['s2p_spikes_cut'] = pickle.load(file)
            # movement
            with open(os.path.join(exp_dir_processed_cut,'wheel.pickle'), "rb") as file: data['wheel_cut'] = pickle.load(file)
            # eye
            with open(os.path.join(exp_dir_processed_cut,'eye_left_cut.pickle'), "rb") as file: data['eye_left_cut'] = pickle.load(file)
            with open(os.path.join(exp_dir_processed_cut,'eye_right_cut.pickle'), "rb") as file: data['eye_right_cut'] = pickle.load(file)

            # trial stimulus data
            data['all_trials'] = read_csv(os.path.join(exp_dir_processed, expID + '_all_trials.csv'))
            roi_count = data['s2p_dF_cut']['dF'].shape[0]
            trial_count = data['all_trials'].shape[0]
            ## stats for dF/F/Spikes
            neural_activity[ch] = {}
            # order(roi,trial)
            # calculate samples to use
            pre_samples = np.arange(np.argmax(data['s2p_dF_cut']['t']>=trial_average_config['pre_interval'][0]),np.argmax(data['s2p_dF_cut']['t']>trial_average_config['pre_interval'][1])-1)
            post_samples = np.arange(np.argmax(data['s2p_dF_cut']['t']>=trial_average_config['post_interval'][0]),np.argmax(data['s2p_dF_cut']['t']>trial_average_config['post_interval'][1])-1)
            # calc means for this time window
            neural_activity[ch]['dF_pre_mean_trials'] = np.nanmean(data['s2p_dF_cut']['dF'][:,:,pre_samples],2)
            neural_activity[ch]['F_pre_mean_trials'] = np.nanmean(data['s2p_F_cut']['F'][:,:,pre_samples],2)
            neural_activity[ch]['spikes_pre_mean_trials'] = np.nanmean(data['s2p_spikes_cut']['Spikes'][:,:,pre_samples],2)
            neural_activity[ch]['dF_post_mean_trials'] = np.nanmean(data['s2p_dF_cut']['dF'][:,:,post_samples],2)
            neural_activity[ch]['F_post_mean_trials'] = np.nanmean(data['s2p_F_cut']['F'][:,:,post_samples],2)
            neural_activity[ch]['spikes_post_mean_trials'] = np.nanmean(data['s2p_spikes_cut']['Spikes'][:,:,post_samples],2)
            # calc medians for this time window
            neural_activity[ch]['dF_pre_median_trials'] = np.nanmedian(data['s2p_dF_cut']['dF'][:,:,pre_samples],2)
            neural_activity[ch]['F_pre_median_trials'] = np.nanmedian(data['s2p_F_cut']['F'][:,:,pre_samples],2)
            neural_activity[ch]['spikes_pre_median_trials'] = np.nanmedian(data['s2p_spikes_cut']['Spikes'][:,:,pre_samples],2)
            neural_activity[ch]['dF_post_median_trials'] = np.nanmedian(data['s2p_dF_cut']['dF'][:,:,post_samples],2)
            neural_activity[ch]['F_post_median_trials'] = np.nanmedian(data['s2p_F_cut']['F'][:,:,post_samples],2)
            neural_activity[ch]['spikes_post_median_trials'] = np.nanmedian(data['s2p_spikes_cut']['Spikes'][:,:,post_samples],2)

        ## stats for wheel
        wheel = {}
        # calculate samples to use
        pre_samples = np.arange(np.argmax(data['wheel_cut']['t']>=trial_average_config['pre_interval'][0]),np.argmax(data['wheel_cut']['t']>trial_average_config['pre_interval'][1])-1)
        post_samples = np.arange(np.argmax(data['wheel_cut']['t']>=trial_average_config['post_interval'][0]),np.argmax(data['wheel_cut']['t']>trial_average_config['post_interval'][1])-1)
        # calc stats for these time windows
        wheel['velocity_pre_mean_trials'] = np.nanmean(data['wheel_cut']['speed'][:,pre_samples],1)
        wheel['velocity_pre_median_trials'] = np.nanmedian(data['wheel_cut']['speed'][:,pre_samples],1)            
        wheel['velocity_pre_max_trials'] = np.nanmax(data['wheel_cut']['speed'][:,pre_samples],1)
        wheel['velocity_pre_min_trials'] = np.nanmin(data['wheel_cut']['speed'][:,pre_samples],1)
        wheel['velocity_post_mean_trials'] = np.nanmean(data['wheel_cut']['speed'][:,post_samples],1)
        wheel['velocity_post_median_trials'] = np.nanmedian(data['wheel_cut']['speed'][:,post_samples],1)            
        wheel['velocity_post_max_trials'] = np.nanmax(data['wheel_cut']['speed'][:,post_samples],1)
        wheel['velocity_post_min_trials'] = np.nanmin(data['wheel_cut']['speed'][:,post_samples],1)

        ## stats for L eye movements
        eye_l = {}
        # calculate samples to use
        pre_samples = np.arange(np.argmax(data['eye_left_cut']['t']>=trial_average_config['pre_interval'][0]),np.argmax(data['eye_left_cut']['t']>trial_average_config['pre_interval'][1])-1)
        post_samples = np.arange(np.argmax(data['eye_left_cut']['t']>=trial_average_config['post_interval'][0]),np.argmax(data['eye_left_cut']['t']>trial_average_config['post_interval'][1])-1)
        # calc stats for these time windows
        # X
        eye_l['x_l_pre_mean_trials'] = np.nanmean(data['eye_left_cut']['x'][:,pre_samples],1)
        eye_l['x_l_pre_median_trials'] = np.nanmedian(data['eye_left_cut']['x'][:,pre_samples],1)
        eye_l['x_l_pre_max_trials'] = np.nanmax(data['eye_left_cut']['x'][:,pre_samples],1)
        eye_l['x_l_pre_min_trials'] = np.nanmin(data['eye_left_cut']['x'][:,pre_samples],1)
        eye_l['x_l_post_mean_trials'] = np.nanmean(data['eye_left_cut']['x'][:,post_samples],1)
        eye_l['x_l_post_median_trials'] = np.nanmedian(data['eye_left_cut']['x'][:,post_samples],1)
        eye_l['x_l_post_max_trials'] = np.nanmax(data['eye_left_cut']['x'][:,post_samples],1)
        eye_l['x_l_post_min_trials'] = np.nanmin(data['eye_left_cut']['x'][:,post_samples],1)
        # Y
        eye_l['y_l_pre_mean_trials'] = np.nanmean(data['eye_left_cut']['y'][:,pre_samples],1) 
        eye_l['y_l_pre_median_trials'] = np.nanmedian(data['eye_left_cut']['y'][:,pre_samples],1)            
        eye_l['y_l_pre_max_trials'] = np.nanmax(data['eye_left_cut']['y'][:,pre_samples],1)            
        eye_l['y_l_pre_min_trials'] = np.nanmin(data['eye_left_cut']['y'][:,pre_samples],1)                    
        eye_l['y_l_post_mean_trials'] = np.nanmean(data['eye_left_cut']['y'][:,post_samples],1) 
        eye_l['y_l_post_median_trials'] = np.nanmedian(data['eye_left_cut']['y'][:,post_samples],1)            
        eye_l['y_l_post_max_trials'] = np.nanmax(data['eye_left_cut']['y'][:,post_samples],1)            
        eye_l['y_l_post_min_trials'] = np.nanmin(data['eye_left_cut']['y'][:,post_samples],1)    
        # Radius
        eye_l['radius_l_pre_mean_trials'] = np.nanmean(data['eye_left_cut']['radius'][:,pre_samples],1) 
        eye_l['radius_l_pre_median_trials'] = np.nanmedian(data['eye_left_cut']['radius'][:,pre_samples],1)            
        eye_l['radius_l_pre_max_trials'] = np.nanmax(data['eye_left_cut']['radius'][:,pre_samples],1)            
        eye_l['radius_l_pre_min_trials'] = np.nanmin(data['eye_left_cut']['radius'][:,pre_samples],1)                    
        eye_l['radius_l_post_mean_trials'] = np.nanmean(data['eye_left_cut']['radius'][:,post_samples],1) 
        eye_l['radius_l_post_median_trials'] = np.nanmedian(data['eye_left_cut']['radius'][:,post_samples],1)            
        eye_l['radius_l_post_max_trials'] = np.nanmax(data['eye_left_cut']['radius'][:,post_samples],1)            
        eye_l['radius_l_post_min_trials'] = np.nanmin(data['eye_left_cut']['radius'][:,post_samples],1)    

        ## stats for R eye movements
        eye_r = {}
        # calculate samples to use
        pre_samples = np.arange(np.argmax(data['eye_right_cut']['t']>=trial_average_config['pre_interval'][0]),np.argmax(data['eye_right_cut']['t']>trial_average_config['pre_interval'][1])-1)
        post_samples = np.arange(np.argmax(data['eye_right_cut']['t']>=trial_average_config['post_interval'][0]),np.argmax(data['eye_right_cut']['t']>trial_average_config['post_interval'][1])-1)
        # calc stats for these time windows
        # X
        eye_r['x_r_pre_mean_trials'] = np.nanmean(data['eye_right_cut']['x'][:,pre_samples],1)
        eye_r['x_r_pre_median_trials'] = np.nanmedian(data['eye_right_cut']['x'][:,pre_samples],1)
        eye_r['x_r_pre_max_trials'] = np.nanmax(data['eye_right_cut']['x'][:,pre_samples],1)
        eye_r['x_r_pre_min_trials'] = np.nanmin(data['eye_right_cut']['x'][:,pre_samples],1)
        eye_r['x_r_post_mean_trials'] = np.nanmean(data['eye_right_cut']['x'][:,post_samples],1)
        eye_r['x_r_post_median_trials'] = np.nanmedian(data['eye_right_cut']['x'][:,post_samples],1)
        eye_r['x_r_post_max_trials'] = np.nanmax(data['eye_right_cut']['x'][:,post_samples],1)
        eye_r['x_r_post_min_trials'] = np.nanmin(data['eye_right_cut']['x'][:,post_samples],1)
        # Y
        eye_r['y_r_pre_mean_trials'] = np.nanmean(data['eye_right_cut']['y'][:,pre_samples],1) 
        eye_r['y_r_pre_median_trials'] = np.nanmedian(data['eye_right_cut']['y'][:,pre_samples],1)            
        eye_r['y_r_pre_max_trials'] = np.nanmax(data['eye_right_cut']['y'][:,pre_samples],1)            
        eye_r['y_r_pre_min_trials'] = np.nanmin(data['eye_right_cut']['y'][:,pre_samples],1)                    
        eye_r['y_r_post_mean_trials'] = np.nanmean(data['eye_right_cut']['y'][:,post_samples],1) 
        eye_r['y_r_post_median_trials'] = np.nanmedian(data['eye_right_cut']['y'][:,post_samples],1)            
        eye_r['y_r_post_max_trials'] = np.nanmax(data['eye_right_cut']['y'][:,post_samples],1)            
        eye_r['y_r_post_min_trials'] = np.nanmin(data['eye_right_cut']['y'][:,post_samples],1)    
        # Radius
        eye_r['radius_r_pre_mean_trials'] = np.nanmean(data['eye_right_cut']['radius'][:,pre_samples],1) 
        eye_r['radius_r_pre_median_trials'] = np.nanmedian(data['eye_right_cut']['radius'][:,pre_samples],1)            
        eye_r['radius_r_pre_max_trials'] = np.nanmax(data['eye_right_cut']['radius'][:,pre_samples],1)            
        eye_r['radius_r_pre_min_trials'] = np.nanmin(data['eye_right_cut']['radius'][:,pre_samples],1)                    
        eye_r['radius_r_post_mean_trials'] = np.nanmean(data['eye_right_cut']['radius'][:,post_samples],1) 
        eye_r['radius_r_post_median_trials'] = np.nanmedian(data['eye_right_cut']['radius'][:,post_samples],1)            
        eye_r['radius_r_post_max_trials'] = np.nanmax(data['eye_right_cut']['radius'][:,post_samples],1)            
        eye_r['radius_r_post_min_trials'] = np.nanmin(data['eye_right_cut']['radius'][:,post_samples],1)

        # save
        # combine all into one 
        trial_average = {}
        trial_average['neural_activity'] = neural_activity
        trial_average['wheel'] = wheel
        trial_average['eye_l'] = eye_l
        trial_average['eye_r'] = eye_r
        trial_average['trial_average_config'] = trial_average_config

        out_filename = trial_average_config['name']+'_ch'+str(ch)+'.pickle'
        with open(os.path.join(exp_dir_processed_trial_average,out_filename), 'wb') as f: pickle.dump(trial_average, f)   

# for debugging:
def main():
# Start timing (tic)
    start_time = time.time()
    trial_average_config = {}
    trial_average_config['userID'] = 'adamranson'
    trial_average_config['expIDs'] = ['2023-03-01_01_ESMT107']
    trial_average_config['chs'] = [0]

    trial_average_config['pre_interval'] = [-0.5, 0.0] 
    trial_average_config['post_interval'] = [0.5, 2.0]
    trial_average_config['name'] = 'trial-0.5_0.0__0.5_2.0'
    run_trial_average_batch(trial_average_config)
    # Stop timing (toc)
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Elapsed time: {elapsed_time:.6f} seconds")

if __name__ == "__main__":
    main()