# example config file for running step 2.
# this file should be saved in the configs folder

from run_step2_batch import run_step2_batch

step2_config = {}

step2_config['userID'] = 'adamranson'
step2_config['expIDs'] = ['2023-10-31_03_ESMT151'] 
step2_config['pre_secs'] = 5
step2_config['post_secs'] = 5
step2_config['run_bonvision'] = True
step2_config['run_s2p_timestamp'] = True
step2_config['run_ephys'] = True
step2_config['run_dlc_timestamp'] = True
step2_config['run_cuttraces'] = True

# run this config
run_step2_batch(step2_config)