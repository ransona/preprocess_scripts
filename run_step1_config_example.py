# example config file for running step 1.
# this file should be saved in the same directory with the filename 'run_step1_config.py' with your configurations 

from run_step1_batch import run_step1_batch

step1_config = {}

step1_config['userID'] = 'adamranson'
step1_config['expIDs'] = ['2023-03-01_01_ESMT107']  # <-- this is a stim artifact experiment
step1_config['suite2p_config'] = 'ch_1_depth_1.npy'
step1_config['runs2p'] = True 
step1_config['rundlc'] = True
step1_config['runfitpupil'] = True
step1_config['jump_queue'] = False # DO NOT CHANGE

# run this config
run_step1_batch(step1_config)