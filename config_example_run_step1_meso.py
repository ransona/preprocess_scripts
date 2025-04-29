# example config file for running step 1.
# this file should be saved in the configs folder

import getpass
from run_step1_batch_meso import run_step1_batch_meso

step1_config = {}
username = getpass.getuser()
step1_config['userID'] = 'adamranson' #username # defines where processed data will be stored and subsequently sought
step1_config['expIDs'] = ['2025-04-10_26_TEST']
# suite2p config will potentially be specific to scan path and also to the roi
# the nested list is for the two scan paths, and witin each scan path, the lists are for the multiple ROIs
# if within the scan path there is only one suite2p config, then this is applied to all rois in that scan path
step1_config['suite2p_config'] = [['ch_1_depth_1_artifact.npy'],['ch_1_depth_1_artifact.npy']]
# step1_config['suite2p_config'] = 'ch_1_depth_9_artifact.npy'
#  step1_config['suite2p_config'] = 'ch_1_2_depth_5_artifact.npy'
step1_config['runs2p'] = True 
step1_config['rundlc'] = False
step1_config['runfitpupil'] = False
step1_config['jump_queue'] = False

# run this config
run_step1_batch_meso(step1_config)