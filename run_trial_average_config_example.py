# example config file for running trial averaging.
# this file should be saved in the configs folder

from run_trial_average_batch import run_trial_average_batch
from pandas import read_csv

trial_average_config = {}

trial_average_config['userID'] = 'adamranson'
trial_average_config['expIDs'] = ['2023-03-01_01_ESMT107']
trial_average_config['pre_interval'] = [-0.5, 0.0] 
trial_average_config['post_interval'] = [0.5, 2.0]
trial_average_config['name'] = 'trial-0.5_0.0__0.5_2.0' 

# run this config
run_trial_average_batch(trial_average_config)