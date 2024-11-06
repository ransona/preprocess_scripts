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

# other setting that can be used in the pipeline if needed by loading the step2 settings file 
settings = {}
settings['neuropil_coeff'] = [0,0.7] # one for each channel, defaults to 0.7 if not set
settings['subtract_overall_frame'] = False
step2_config['settings'] = settings

# run this config
run_step2_batch(step2_config)