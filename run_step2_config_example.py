# example config file for running step 2.
# this file should be saved in the same directory with the filename 'run_step2_config.py' with your configurations 

from run_step2_batch import run_step2_batch

step2_config = {}

step2_config['userID'] = 'adamranson'
step2_config['expIDs'] = ['2023-03-01_01_ESMT107']  # <-- this is a stim artifact experiment
step2_config['pre_secs'] = 5
step2_config['post_secs'] = 5
step2_config['run_bonvision'] = True
step2_config['run_s2p_timestamp'] = True
step2_config['run_ephys'] = True
step2_config['run_dlc_timestamp'] = True
step2_config['run_cuttraces'] = True

# run this config
run_step2_batch(step2_config)