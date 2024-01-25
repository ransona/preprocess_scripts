# example config file for running step 1.
# this file should be saved in the configs folder
import getpass
from run_step1_batch import run_step1_batch

step1_config = {}
username = getpass.getuser()
step1_config['userID'] = username # defines where processed data will be stored and subsequently sought
step1_config['expIDs'] = ['2023-10-31_03_ESMT151'] 
step1_config['suite2p_config'] = 'ch_1_depth_1_axon.npy'
step1_config['runs2p'] = True 
step1_config['rundlc'] = True
step1_config['runfitpupil'] = True
step1_config['jump_queue'] = False # DO NOT CHANGE

# run this config
run_step1_batch(step1_config)  