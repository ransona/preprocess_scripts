# example config file for running step 1.
# this file should be saved in the configs folder

import getpass
from run_step1_batch import run_step1_batch

step1_config = {}
username = getpass.getuser()
step1_config['userID'] = username # defines where processed data will be stored and subsequently sought
step1_config['expIDs'] = ['2024-10-28_06_ESMT190']
step1_config['suite2p_config'] = 'ch_1_depth_1.npy'
step1_config['runs2p'] = True 
step1_config['rundlc'] = True
step1_config['runfitpupil'] = True
step1_config['suite2p_env'] = 'suite2p'

# run this config
run_step1_batch(step1_config)