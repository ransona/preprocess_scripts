import pickle
import os
import organise_paths
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

userID = 'adamranson'
expID = '2025-03-05_02_ESMT204'  

# the organise_paths.find_paths(userID, expID) gives you various useful
# paths based on an experiment ID
animalID, remote_repository_root, processed_root, exp_dir_processed, exp_dir_raw = organise_paths.find_paths(userID, expID)
# os.path.join combined strings to make a path that will work on whatever 
# operating system the function is run on
exp_dir_processed_recordings = os.path.join(exp_dir_processed,'recordings')

Ch = 0
with open(os.path.join(exp_dir_processed_recordings,('s2p_ch' + str(Ch)+'.pickle')),'rb') as file: ca_data = pickle.load(file)

plt.figure()
# Define the time range for x-axis
t_min = ca_data['t'][0]
t_max = ca_data['t'][-1]
plt.imshow(ca_data['dF'], aspect='auto', extent=[t_min, t_max, 0, ca_data['dF'].shape[0]], origin='upper')
plt.colorbar(label='dF/F')
plt.xlabel('Time (s)')
plt.ylabel('Signal Index')
plt.title('Ca Imaging Data')
plt.show()
x=0