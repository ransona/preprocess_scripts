# example config file for running step 1.
# this file should be saved in the configs folder
# this version is for running multiple experiments in the same suite2p run

import getpass
from run_step1_batch import run_step1_batch

step1_config = {}
username = getpass.getuser()
step1_config['userID'] = username # defines where processed data will be stored and subsequently sought
step1_config['expIDs'] = [['2023-02-28_13_ESMT116','2023-02-28_14_ESMT116']]
step1_config['suite2p_config'] = 'ch_1_depth_1.npy'
step1_config['runs2p'] = True 
step1_config['rundlc'] = True
step1_config['runfitpupil'] = True
step1_config['suite2p_env'] = 'suite2p'
# other setting that can be used in the pipeline if needed by loading the command file 
settings = {}
settings['neuropil_coeff'] = [0.7,0.7] # one for each channel, defaults to 0.7 if not set
settings['subtract_overall_frame'] = False
step1_config['settings'] = settings

# run this config
run_step1_batch(step1_config)